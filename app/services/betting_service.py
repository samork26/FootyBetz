# betting_services.py

from ..models import Bet, UserPoints

def settle_bets_for_match(match):
    """
    Settle bets for a finished match using FanDuel odds.
    For each bet placed on the match, if the bet's outcome matches the match result,
    award the user with points equal to the potential winnings (calculated as bet amount * odds).
    Assumes that the Bet model has a Boolean field 'settled' (default False).
    """
    # Determine match result based on scores
    if match.home_score > match.away_score:
        result = 'home_win'
    elif match.home_score < match.away_score:
        result = 'away_win'
    else:
        result = 'draw'
    
    # Retrieve all unsettled bets for this match
    bets = Bet.objects.filter(match=match, settled=False)
    
    for bet in bets:
        if bet.bet_type == result:
            # User's bet was correct—award points (total return including stake)
            user_points, _ = UserPoints.objects.get_or_create(user=bet.user)
            user_points.points += bet.potential_winnings  # e.g., 5 * 1.40 = 7 points
            user_points.save()
        # Mark bet as settled so it isn't processed again
        bet.settled = True
        bet.save()
