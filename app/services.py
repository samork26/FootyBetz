import os
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Team, Match, MatchOdds, LeagueTable

class FootballDataService:
    BASE_URL = "http://api.football-data.org/v4"
    ODDS_API_KEY = "8bd4cf8687f52a1a48641734c3126a8b"
    ODDS_BASE_URL = "https://api.the-odds-api.com/v4/sports"
    
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_DATA_API_KEY')
        self.headers = {'X-Auth-Token': self.api_key}
    
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