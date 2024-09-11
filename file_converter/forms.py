from django import forms
from .models import VideoFile

class VideoFileForm(forms.ModelForm):
    class Meta:
        model = VideoFile
        fields = ['video']