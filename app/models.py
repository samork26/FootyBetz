from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100)
    logo_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name

class LeagueTable(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='standing')
    position = models.IntegerField()
    played_games = models.IntegerField()
    won = models.IntegerField()
    draw = models.IntegerField()
    lost = models.IntegerField()
    goals_for = models.IntegerField()
    goals_against = models.IntegerField()
    goal_difference = models.IntegerField()
    points = models.IntegerField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.team.name} - Position {self.position} ({self.points} points)"

class Match(models.Model):
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    match_date = models.DateTimeField()
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"

class MatchOdds(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='odds')
    home_win = models.FloatField(null=True, blank=True)
    draw = models.FloatField(null=True, blank=True)
    away_win = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Odds for {self.match}"
