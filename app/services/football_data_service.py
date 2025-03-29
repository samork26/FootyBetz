import os
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from ..models import Team, Match, MatchOdds, LeagueTable
import logging

logger = logging.getLogger(__name__)

class FootballDataService:
    BASE_URL = "http://api.football-data.org/v4"
    ODDS_BASE_URL = "https://api.the-odds-api.com/v4/sports"
    
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_DATA_API_KEY')
        self.headers = {'X-Auth-Token': self.api_key}
        self.odds_api_key = os.getenv('ODDS_API_KEY')
        self.odds_base_url = "https://api.the-odds-api.com/v4"
    
    def fetch_upcoming_matches(self):
        """Fetch upcoming Premier League matches"""
        # Premier League competition ID
        competition_id = "PL"
        
        # Get matches for the next 30 days
        from_date = datetime.now().strftime("%Y-%m-%d")
        to_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/competitions/{competition_id}/matches"
        params = {
            'dateFrom': from_date,
            'dateTo': to_date,
            'status': 'SCHEDULED'
        }
        
        try:
            #print(f"Fetching matches from {from_date} to {to_date}")
            #print(f"URL: {url}")
            #print(f"Headers: {self.headers}")
            
            response = requests.get(url, headers=self.headers, params=params)
            #print(f"Response status code: {response.status_code}")
            #print(f"Response content: {response.text[:500]}...")  # Print first 500 chars of response
            
            response.raise_for_status()
            data = response.json()
            #print(f"Number of matches found: {len(data.get('matches', []))}")
            return data.get('matches', [])
        except requests.RequestException as e:
            print(f"Error fetching matches: {e}")
            return []

    def fetch_odds(self, match):
        """Fetch odds for a specific match"""
        try:
            # Format the teams for the odds API
            teams = f"{match.home_team.name} vs {match.away_team.name}"
            
            # Get odds for soccer matches
            url = f"{self.ODDS_BASE_URL}/soccer_epl/odds"
            params = {
                'apiKey': self.ODDS_API_KEY,
                'regions': 'eu',
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Find the matching game
            for game in data:
                if game['home_team'] == match.home_team.name and game['away_team'] == match.away_team.name:
                    # Extract odds for home win, away win, and draw
                    odds = {}
                    for market in game['bookmakers'][0]['markets'][0]['outcomes']:
                        if market['name'] == match.home_team.name:
                            odds['home_win'] = market['price']
                        elif market['name'] == match.away_team.name:
                            odds['away_win'] = market['price']
                        elif market['name'] == 'Draw':
                            odds['draw'] = market['price']
                    
                    # Update or create MatchOdds
                    match_odds, created = MatchOdds.objects.update_or_create(
                        match=match,
                        defaults={
                            'home_win_odds': odds.get('home_win'),
                            'away_win_odds': odds.get('away_win'),
                            'draw_odds': odds.get('draw')
                        }
                    )
                    return match_odds
            
            return None
        except Exception as e:
            print(f"Error fetching odds: {e}")
            return None

    def update_matches(self):
        """Update matches in the database"""
        matches = self.fetch_upcoming_matches()
        print(f"Processing {len(matches)} matches")
        
        for match_data in matches:
            try:
                # Get or create teams
                home_team, _ = Team.objects.get_or_create(
                    name=match_data['homeTeam']['name'],
                    defaults={
                        'short_name': match_data['homeTeam']['shortName'],
                        'logo_url': match_data['homeTeam']['crest']
                    }
                )
                
                away_team, _ = Team.objects.get_or_create(
                    name=match_data['awayTeam']['name'],
                    defaults={
                        'short_name': match_data['awayTeam']['shortName'],
                        'logo_url': match_data['awayTeam']['crest']
                    }
                )
                
                # Update logo URLs if they've changed
                if home_team.logo_url != match_data['homeTeam']['crest']:
                    home_team.logo_url = match_data['homeTeam']['crest']
                    home_team.save()
                
                if away_team.logo_url != match_data['awayTeam']['crest']:
                    away_team.logo_url = match_data['awayTeam']['crest']
                    away_team.save()
                
                # Convert match date to timezone-aware datetime
                match_date = datetime.strptime(match_data['utcDate'], "%Y-%m-%dT%H:%M:%SZ")
                match_date = timezone.make_aware(match_date)
                
                # Map API status to our model status
                status_mapping = {
                    'SCHEDULED': 'scheduled',
                    'LIVE': 'live',
                    'IN_PROGRESS': 'live',
                    'PAUSED': 'live',
                    'FINISHED': 'finished',
                    'POSTPONED': 'postponed',
                    'SUSPENDED': 'cancelled',
                    'CANCELLED': 'cancelled'
                }
                
                status = status_mapping.get(match_data['status'], 'scheduled')
                
                # Update or create match
                match, created = Match.objects.update_or_create(
                    home_team=home_team,
                    away_team=away_team,
                    match_date=match_date,
                    defaults={
                        'venue': match_data.get('venue', ''),
                        'status': status,
                        'home_score': match_data['score']['fullTime']['home'],
                        'away_score': match_data['score']['fullTime']['away'],
                        'matchweek': match_data['matchday']
                    }
                )
                print(f"{'Created' if created else 'Updated'} match: {match}")
                
            except Exception as e:
                print(f"Error processing match: {e}")
                print(f"Match data: {match_data}")

    def fetch_league_table(self):
        """Fetch Premier League table"""
        competition_id = "PL"
        url = f"{self.BASE_URL}/competitions/{competition_id}/standings"
        
        try:
            print("Fetching league table...")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            standings = data['standings'][0]['table']
            print(f"Found {len(standings)} teams in the table")
            
            for standing in standings:
                team_data = standing['team']
                team, _ = Team.objects.get_or_create(
                    name=team_data['name'],
                    defaults={
                        'short_name': team_data['shortName'],
                        'logo_url': team_data['crest']
                    }
                )
                
                # Update team logo if it has changed
                if team.logo_url != team_data['crest']:
                    team.logo_url = team_data['crest']
                    team.save()
                
                # Update or create league table entry
                LeagueTable.objects.update_or_create(
                    team=team,
                    defaults={
                        'position': standing['position'],
                        'played_games': standing['playedGames'],
                        'won': standing['won'],
                        'draw': standing['draw'],
                        'lost': standing['lost'],
                        'points': standing['points'],
                        'goals_for': standing['goalsFor'],
                        'goals_against': standing['goalsAgainst'],
                        'goal_difference': standing['goalDifference']
                    }
                )
            
            return True
        except Exception as e:
            print(f"Error fetching league table: {e}")
            return False

    def get_odds_for_match(self, match):
        """Get odds for a specific match from The Odds API"""
        try:
            # First, get the event ID for this match
            event_url = f"{self.odds_base_url}/sports/soccer_epl/events"
            
            # Use the match date for the time window
            match_time = match.match_date
            # Convert to EST
            est = timezone.get_fixed_timezone(-300)  # EST is UTC-5
            match_time_est = match_time.astimezone(est)
            
            # Set a 1-hour window around the match time
            start_time = match_time_est - timedelta(minutes=30)
            end_time = match_time_est + timedelta(minutes=60)
            
            # Convert back to UTC for API call
            start_time_utc = start_time.astimezone(timezone.utc)
            end_time_utc = end_time.astimezone(timezone.utc)
            
            event_params = {
                'apiKey': self.odds_api_key,
                'dateFormat': 'iso',
                'commenceTimeFrom': start_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'commenceTimeTo': end_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            logger.info(f"Fetching events for match: {match.home_team.name} vs {match.away_team.name}")
            logger.info(f"Match time (EST): {match_time_est.strftime('%Y-%m-%d %I:%M %p %Z')}")
            logger.info(f"Time window (EST): {start_time.strftime('%Y-%m-%d %I:%M %p %Z')} to {end_time.strftime('%Y-%m-%d %I:%M %p %Z')}")
            
            event_response = requests.get(event_url, params=event_params)
            event_response.raise_for_status()
            events = event_response.json()
            logger.info(f"Found {len(events)} events")

            # Find the matching event by team names
            event_id = None
            for event in events:
                # Clean team names for comparison
                event_home = event['home_team'].lower().strip()
                event_away = event['away_team'].lower().strip()
                match_home = match.home_team.name.lower().strip()
                match_away = match.away_team.name.lower().strip()
                
                # Check for partial matches using string containment
                home_match = match_home in event_home or event_home in match_home
                away_match = match_away in event_away or event_away in match_away
                
                if home_match and away_match:
                    event_id = event['id']
                    logger.info(f"Found matching event ID: {event_id}")
                    logger.info(f"Matched teams: {event_home} vs {event_away}")
                    logger.info(f"Original teams: {match_home} vs {match_away}")
                    break
            #print(events)
            if not event_id:
                logger.warning(f"No event ID found for match: {match.home_team.name} vs {match.away_team.name}")
                return None

            # Get odds for the specific event
            odds_url = f"{self.odds_base_url}/sports/soccer_epl/events/{event_id}/odds"
            odds_params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h',
                'oddsFormat': 'decimal',
                'bookmakers': 'fanduel'
            }

            logger.info(f"Fetching odds for event ID: {event_id}")
            odds_response = requests.get(odds_url, params=odds_params)
            odds_response.raise_for_status()
            odds_data = odds_response.json()
            logger.info(f"Received odds data: {odds_data}")

            if not odds_data or 'bookmakers' not in odds_data:
                logger.warning(f"No odds data found for event ID: {event_id}")
                return None

            # Extract FanDuel odds
            fanduel_odds = None
            for bookmaker in odds_data['bookmakers']:
                if bookmaker['key'] == 'fanduel':
                    fanduel_odds = bookmaker
                    logger.info("Found FanDuel odds")
                    break

            if not fanduel_odds or 'markets' not in fanduel_odds:
                logger.warning(f"No FanDuel odds found for event ID: {event_id}")
                return None

            # Extract the h2h market odds
            h2h_market = next((market for market in fanduel_odds['markets'] if market['key'] == 'h2h'), None)
            if not h2h_market or 'outcomes' not in h2h_market:
                logger.warning(f"No h2h market found for event ID: {event_id}")
                return None

            # Print raw odds data for debugging
            logger.info("Raw h2h market outcomes:")
            for outcome in h2h_market['outcomes']:
                logger.info(f"Outcome: {outcome['name']}, Price: {outcome['price']}")

            # Create odds dictionary
            odds_dict = {}
            
            # Get the event teams from the API response
            event_home_team = odds_data['home_team'].lower()
            event_away_team = odds_data['away_team'].lower()
            
            logger.info(f"Event teams: {event_home_team} vs {event_away_team}")
            
            for outcome in h2h_market['outcomes']:
                outcome_name = outcome['name'].lower()
                price = outcome['price']
                
                # Log each outcome as we process it
                logger.info(f"Processing outcome: {outcome_name} with price {price}")
                
                # Match based on event teams rather than match teams
                if outcome_name == event_home_team:
                    odds_dict['home_win_odds'] = price
                    logger.info(f"Set home win odds: {price}")
                elif outcome_name == event_away_team:
                    odds_dict['away_win_odds'] = price
                    logger.info(f"Set away win odds: {price}")
                elif outcome_name == 'draw':
                    odds_dict['draw_odds'] = price
                    logger.info(f"Set draw odds: {price}")

            # Log final odds dictionary
            logger.info(f"Final odds dictionary: {odds_dict}")
            
            # Verify we have all three outcomes
            if not all(key in odds_dict for key in ['home_win_odds', 'away_win_odds', 'draw_odds']):
                logger.warning("Missing some odds outcomes:")
                logger.warning(f"Home win odds: {'home_win_odds' in odds_dict}")
                logger.warning(f"Away win odds: {'away_win_odds' in odds_dict}")
                logger.warning(f"Draw odds: {'draw_odds' in odds_dict}")
                logger.warning(f"Available outcomes: {[outcome['name'] for outcome in h2h_market['outcomes']]}")

            return odds_dict

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_odds_for_match: {str(e)}")
            return None 