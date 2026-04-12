from django.db import models
from django.contrib.auth.models import User

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    word_count = models.IntegerField()
    char_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class LoginAttempt(models.Model):
    ip = models.CharField(max_length=50)
    attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f'{self.ip} - {self.attempts}'


