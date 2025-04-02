import os
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .models import Team, Match, MatchOdds, LeagueTable
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

    def convert_to_american_odds(self, decimal_odds):
        """Convert decimal odds to American odds"""
        if decimal_odds >= 2.00:
            return round((decimal_odds - 1) * 100)
        else:
            return round(-100 / (decimal_odds - 1))

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
            
            event_response = requests.get(event_url, params=event_params)
            event_response.raise_for_status()
            events = event_response.json()

            # Find the matching event by team names
            event_id = None
            for event in events:
                event_home = event['home_team'].lower().strip()
                event_away = event['away_team'].lower().strip()
                match_home = match.home_team.name.lower().strip()
                match_away = match.away_team.name.lower().strip()
                
                home_match = match_home in event_home or event_home in match_home
                away_match = match_away in event_away or event_away in match_away
                
                if home_match and away_match:
                    event_id = event['id']
                    break

            if not event_id:
                logger.warning(f"No event ID found for match: {match.home_team.name} vs {match.away_team.name}")
                return None

            # Get odds for the specific event
            odds_url = f"{self.odds_base_url}/sports/soccer_epl/events/{event_id}/odds"
            odds_params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }

            odds_response = requests.get(odds_url, params=odds_params)
            odds_response.raise_for_status()
            odds_data = odds_response.json()

            if not odds_data or 'bookmakers' not in odds_data:
                logger.warning(f"No odds data found for event ID: {event_id}")
                return None

            # Get the event teams from the API response
            event_home_team = odds_data['home_team'].lower()
            event_away_team = odds_data['away_team'].lower()
            
            # Initialize odds structure
            odds_structure = {
                'bookmakers': [],
                'best_odds': {
                    'home_win': {'decimal': 0, 'american': 0, 'bookmaker': None},
                    'away_win': {'decimal': 0, 'american': 0, 'bookmaker': None},
                    'draw': {'decimal': 0, 'american': 0, 'bookmaker': None}
                },
                'arbitrage': None
            }

            # Process each bookmaker's odds
            for bookmaker in odds_data['bookmakers']:
                bookmaker_odds = {
                    'name': bookmaker['title'],
                    'home_win': {'decimal': None, 'american': None},
                    'away_win': {'decimal': None, 'american': None},
                    'draw': {'decimal': None, 'american': None}
                }

                # Find the h2h market
                h2h_market = next((market for market in bookmaker['markets'] if market['key'] == 'h2h'), None)
                if h2h_market and 'outcomes' in h2h_market:
                    for outcome in h2h_market['outcomes']:
                        outcome_name = outcome['name'].lower()
                        decimal_price = outcome['price']
                        american_price = self.convert_to_american_odds(decimal_price)
                        
                        if outcome_name == event_home_team:
                            bookmaker_odds['home_win'] = {'decimal': decimal_price, 'american': american_price}
                        elif outcome_name == event_away_team:
                            bookmaker_odds['away_win'] = {'decimal': decimal_price, 'american': american_price}
                        elif outcome_name == 'draw':
                            bookmaker_odds['draw'] = {'decimal': decimal_price, 'american': american_price}

                # Only add bookmaker if it has all three outcomes
                if all(bookmaker_odds[key]['decimal'] is not None for key in ['home_win', 'away_win', 'draw']):
                    odds_structure['bookmakers'].append(bookmaker_odds)
                    
                    # Update best odds
                    if bookmaker_odds['home_win']['decimal'] > odds_structure['best_odds']['home_win']['decimal']:
                        odds_structure['best_odds']['home_win'] = {
                            'decimal': bookmaker_odds['home_win']['decimal'],
                            'american': bookmaker_odds['home_win']['american'],
                            'bookmaker': bookmaker['title']
                        }
                    
                    if bookmaker_odds['away_win']['decimal'] > odds_structure['best_odds']['away_win']['decimal']:
                        odds_structure['best_odds']['away_win'] = {
                            'decimal': bookmaker_odds['away_win']['decimal'],
                            'american': bookmaker_odds['away_win']['american'],
                            'bookmaker': bookmaker['title']
                        }
                    
                    if bookmaker_odds['draw']['decimal'] > odds_structure['best_odds']['draw']['decimal']:
                        odds_structure['best_odds']['draw'] = {
                            'decimal': bookmaker_odds['draw']['decimal'],
                            'american': bookmaker_odds['draw']['american'],
                            'bookmaker': bookmaker['title']
                        }

            # Calculate arbitrage opportunity
            home_odds = odds_structure['best_odds']['home_win']['decimal']
            away_odds = odds_structure['best_odds']['away_win']['decimal']
            
            # Calculate implied probabilities
            home_prob = 1 / home_odds
            away_prob = 1 / away_odds
            
            # Sum of probabilities
            total_prob = home_prob + away_prob
            
            # If total probability is less than 1, there's an arbitrage opportunity
            if total_prob < 1:
                # Calculate stakes for $1000 total bet
                total_bankroll = 1000
                arb_sum = total_prob
                
                home_stake = round((total_bankroll * home_prob) / arb_sum, 2)
                away_stake = round((total_bankroll * away_prob) / arb_sum, 2)
                
                # Calculate potential profit
                home_profit = round(home_stake * home_odds - total_bankroll, 2)
                away_profit = round(away_stake * away_odds - total_bankroll, 2)
                
                odds_structure['arbitrage'] = {
                    'exists': True,
                    'home_stake': home_stake,
                    'away_stake': away_stake,
                    'home_profit': home_profit,
                    'away_profit': away_profit,
                    'home_bookmaker': odds_structure['best_odds']['home_win']['bookmaker'],
                    'away_bookmaker': odds_structure['best_odds']['away_win']['bookmaker']
                }
            else:
                odds_structure['arbitrage'] = {
                    'exists': False,
                    'total_probability': round(total_prob * 100, 2)
                }

            return odds_structure

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_odds_for_match: {str(e)}")
            return None 