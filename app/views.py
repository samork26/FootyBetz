from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from pytz import timezone as pytz_timezone
from .models import Match, MatchOdds, LeagueTable, Team
from .services import FootballDataService
import os
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.urls import reverse

def home(request):
    if request.user.is_authenticated:
        service = FootballDataService()
        service.fetch_league_table()
        standings = LeagueTable.objects.all().order_by('position')
        return render(request, 'index.html', {
            'standings': standings
        })
    return render(request, 'index.html')

def epl(request):
    print("Starting EPL view...")
    print(f"API Key: {os.getenv('FOOTBALL_DATA_API_KEY')}")
    # Update matches from API
    service = FootballDataService()
    print("Created FootballDataService instance")
    
    print("Calling update_matches...")
    service.update_matches()
    print("Finished update_matches")
    
    # Get upcoming matches
    print("Fetching matches from database...")
    upcoming_matches = Match.objects.filter(
        match_date__gte=timezone.now(),
        status='scheduled'
    ).order_by('match_date')
    print(f"Found {upcoming_matches.count()} matches in database")
    
    # Set timezone to EST
    est = pytz_timezone('America/New_York')
    
    context = {
        'matches': upcoming_matches,
        'user_timezone': est,
    }
    return render(request, 'epl.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home') 
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

def match_details(request, match_id):
    try:
        match = Match.objects.get(id=match_id)
        service = FootballDataService()
        
        # Try to get existing odds
        try:
            odds = match.odds
        except Match.odds.RelatedObjectDoesNotExist:
            odds = None
        
        # If no odds exist, fetch them
        if not odds:
            print(f"Fetching odds for match: {match}")
            odds = service.fetch_odds(match)
        
        # Set timezone to EST
        est = pytz_timezone('America/New_York')
        
        context = {
            'match': match,
            'odds': odds,
            'user_timezone': est,
        }
        return render(request, 'match_details.html', context)
    except Match.DoesNotExist:
        messages.error(request, 'Match not found.')
        return redirect('epl')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    return render(request, 'signup.html')

@require_http_methods(["GET"])
def get_matches(request):
    service = FootballDataService()
    service.update_matches()
    
    matches = Match.objects.filter(
        match_date__gte=timezone.now(),
        status='scheduled'
    ).order_by('match_date')
    
    matches_data = []
    for match in matches:
        matches_data.append({
            'id': match.id,
            'home_team': match.home_team.name,
            'away_team': match.away_team.name,
            'match_date': match.match_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': match.status
        })
    
    return JsonResponse({'matches': matches_data})