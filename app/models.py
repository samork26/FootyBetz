from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=3, blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class LeagueTable(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='standing')
    position = models.IntegerField()
    played_games = models.IntegerField()
    won = models.IntegerField()
    draw = models.IntegerField()
    lost = models.IntegerField()
    points = models.IntegerField()
    goals_for = models.IntegerField()
    goals_against = models.IntegerField()
    goal_difference = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.position}. {self.team.name} - {self.points} points"

class Match(models.Model):
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    match_date = models.DateTimeField()
    venue = models.CharField(max_length=100, default='TBD')
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed')
    ], default='scheduled')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    competition = models.CharField(max_length=100, default='Premier League')
    matchweek = models.IntegerField(default=1)
    odds_api_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['match_date']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.match_date.strftime('%Y-%m-%d %H:%M')}"

class MatchOdds(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='odds')
    home_win_odds = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    away_win_odds = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    draw_odds = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Odds for {self.match}"

class UserPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Points: {self.points}"

class Bet(models.Model):
    BET_CHOICES = [
        ('home_win', 'Home Win'),
        ('away_win', 'Away Win'),
        ('draw', 'Draw'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    bet_type = models.CharField(max_length=10, choices=BET_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    potential_winnings = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_settled = models.BooleanField(default=False)
    won = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'match']  # One bet per user per match

    def __str__(self):
        return f"{self.user.username} bet {self.amount} on {self.get_bet_type_display()} for {self.match}"

    def calculate_potential_winnings(self):
        odds = self.match.odds
        if self.bet_type == 'home_win':
            return self.amount * odds.home_win_odds
        elif self.bet_type == 'away_win':
            return self.amount * odds.away_win_odds
        else:  # draw
            return self.amount * odds.draw_odds

    def settle_bet(self):
        if self.match.status != 'finished':
            return False

        if self.is_settled:
            return True

        # Determine if bet was won
        if self.bet_type == 'home_win':
            self.won = self.match.home_score > self.match.away_score
        elif self.bet_type == 'away_win':
            self.won = self.match.home_score < self.match.away_score
        else:  # draw
            self.won = self.match.home_score == self.match.away_score

        # Update user points
        user_points = UserPoints.objects.get(user=self.user)
        if self.won:
            user_points.points += self.potential_winnings
        else:
            user_points.points -= self.amount

        user_points.save()
        self.is_settled = True
        self.save()
        return True
