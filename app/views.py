from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from pytz import timezone as pytz_timezone
from .models import Match, MatchOdds, LeagueTable, Team, UserPoints, Bet
from .services.football_data_service import FootballDataService
import os
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.db import transaction
from decimal import Decimal
from decimal import InvalidOperation

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
        username = request.POST.get('login')
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

@login_required
def match_details(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Get or create user points
    user_points, created = UserPoints.objects.get_or_create(user=request.user)
    
    # Get user's bet for this match if it exists
    user_bet = Bet.objects.filter(user=request.user, match=match).first()
    
    # Handle betting POST request
    if request.method == 'POST':
        # Check if match has started
        if match.status != 'scheduled':
            messages.error(request, 'Betting is closed for this match.')
            return redirect('match_details', match_id=match_id)
        
        # Check if user already has a bet
        if user_bet:
            messages.error(request, 'You have already placed a bet on this match.')
            return redirect('match_details', match_id=match_id)
        
        bet_type = request.POST.get('bet_type')
        try:
            amount = Decimal(request.POST.get('amount', 0))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid bet amount.')
            return redirect('match_details', match_id=match_id)
        
        # Validate bet amount
        if amount <= 0:
            messages.error(request, 'Bet amount must be greater than 0.')
            return redirect('match_details', match_id=match_id)
        
        if amount > user_points.points:
            messages.error(request, 'You do not have enough points for this bet.')
            return redirect('match_details', match_id=match_id)
        
        # Calculate potential winnings before creating the bet
        if bet_type == 'home_win':
            potential_winnings = amount * match.odds.home_win_odds
        elif bet_type == 'away_win':
            potential_winnings = amount * match.odds.away_win_odds
        else:  # draw
            potential_winnings = amount * match.odds.draw_odds
        
        # Create bet with calculated potential winnings
        with transaction.atomic():
            bet = Bet.objects.create(
                user=request.user,
                match=match,
                bet_type=bet_type,
                amount=amount,
                potential_winnings=potential_winnings
            )
            
            # Deduct points from user
            user_points.points -= amount
            user_points.save()
        
        messages.success(request, f'Bet placed successfully! Potential winnings: {bet.potential_winnings:.2f} points')
        return redirect('match_details', match_id=match_id)
    
    # Get odds for the match
    if not match.odds:
        football_service = FootballDataService()
        odds_data = football_service.get_odds_for_match(match)
        if odds_data:
            match.odds = MatchOdds.objects.create(
                match=match,
                home_win_odds=odds_data['home_win_odds'],
                away_win_odds=odds_data['away_win_odds'],
                draw_odds=odds_data['draw_odds']
            )
    
    context = {
        'match': match,
        'user_points': user_points,
        'user_bet': user_bet,
    }
    return render(request, 'match_details.html', context)

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