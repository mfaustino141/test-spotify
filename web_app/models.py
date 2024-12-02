from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class WrappedData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField()
    top_artists = models.JSONField()
    top_tracks = models.JSONField()
    top_genres = models.JSONField()
    listening_stats = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    
class SpotifyWrapped(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    date = models.DateField(default=timezone.now)
    time = models.TimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    user_data = models.TextField(blank=True, null=True) 
