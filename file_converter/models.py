from django.db import models

class VideoFile(models.Model):
    video = models.FileField(upload_to='videos/')
    converted_audio = models.FileField(upload_to='audios/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)