from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from pytube import YouTube
from django.http import HttpResponse
import os
import re
import logging

logger = logging.getLogger(__name__)

@login_required
def home(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        logger.debug(f"Received URL: {url}")
        
        # Validate the YouTube URL
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
        )
        if not youtube_regex.match(url):
            logger.error("Invalid YouTube URL")
            return render(request, 'ytdownloader/home.html', {'error': 'Invalid YouTube URL'})
        
        if url:
            try:
                yt = YouTube(url)
                stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
                if not stream:
                    logger.error("No suitable stream found")
                    return render(request, 'ytdownloader/home.html', {'error': 'No suitable stream found'})
                
                # Get the default Downloads folder path on Windows
                downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
                logger.debug(f"Downloads path: {downloads_path}")
                stream.download(output_path=downloads_path, filename='video.mp4')
                file_path = os.path.join(downloads_path, 'video.mp4')
                logger.debug(f"File path: {file_path}")
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='video/mp4')
                    response['Content-Disposition'] = f'attachment; filename="video.mp4"'
                    return response
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error downloading video: {e}"})
    return render(request, 'ytdownloader/home.html')