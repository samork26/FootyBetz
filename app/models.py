from django.db import models

class MyModel(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=3)
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
    venue = models.CharField(max_length=100)
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
    matchweek = models.IntegerField()
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
