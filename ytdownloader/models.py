from django.db import models
from django.contrib.auth.models import User

class YouTubeDownload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()
    format_id = models.CharField(max_length=10)
    thumbnail = models.URLField(default="")
    title = models.CharField(max_length=200)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title