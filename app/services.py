import os
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Team, Match

class FootballDataService:
    BASE_URL = "http://api.football-data.org/v4"
    
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
            print(f"Fetching matches from {from_date} to {to_date}")
            print(f"URL: {url}")
            print(f"Headers: {self.headers}")
            
            response = requests.get(url, headers=self.headers, params=params)
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}...")  # Print first 500 chars of response
            
            response.raise_for_status()
            data = response.json()
            print(f"Number of matches found: {len(data.get('matches', []))}")
            return data.get('matches', [])
        except requests.RequestException as e:
            print(f"Error fetching matches: {e}")
            return []

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