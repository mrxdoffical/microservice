from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import yt_dlp
import os
import re
import logging

logger = logging.getLogger(__name__)

@login_required
def home(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        format_id = request.POST.get('format_id')
        logger.debug(f"Received URL: {url}")
        
        # Validate the YouTube URL
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
        )
        if not youtube_regex.match(url):
            logger.error("Invalid YouTube URL")
            return render(request, 'ytdownloader/home.html', {'error': 'Invalid YouTube URL'})
        
        if url and not format_id:
            try:
                ydl_opts = {}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    formats = info_dict.get('formats', [])
                    
                    # Filter for progressive streams (video + audio)
                    progressive_streams = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') != 'none']
                    
                    return render(request, 'ytdownloader/home.html', {'formats': progressive_streams, 'url': url})
            except Exception as e:
                logger.error(f"Error fetching video formats: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error fetching video formats: {e}"})
        
        if url and format_id:
            try:
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        percent = d['_percent_str']
                        print(f"Download progress: {percent}")

                ydl_opts = {
                    'format': format_id,
                    'outtmpl': os.path.join(os.path.expanduser('~'), 'Downloads', 'video.mp4'),
                    'progress_hooks': [progress_hook]
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                file_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'video.mp4')
                logger.debug(f"File path: {file_path}")
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='video/mp4')
                    response['Content-Disposition'] = f'attachment; filename="video.mp4"'
                    return response
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error downloading video: {e}"})
    return render(request, 'ytdownloader/home.html')