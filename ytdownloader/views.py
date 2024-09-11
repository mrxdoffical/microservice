# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import yt_dlp
import os
import re
import logging
import urllib.parse
from .models import YouTubeDownload

logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    # Replace any characters that are not allowed in filenames with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

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
                    
                    # Define common formats and qualities
                    common_formats = {
                        'mp4': ['360p', '480p', '720p', '1080p'],
                        'mp3': ['128k', '192k', '256k', '320k']
                    }
                    
                    # Filter for common formats and qualities
                    filtered_formats = [
                        {
                            'format_id': f['format_id'],
                            'format_note': f.get('format_note', 'N/A'),
                            'ext': f['ext'],
                            'resolution': f.get('resolution', 'audio only') if f.get('vcodec') == 'none' else f.get('resolution', 'N/A'),
                            'filesize': f.get('filesize', 0)
                        }
                        for f in formats
                        if f['ext'] in common_formats and f.get('format_note') in common_formats[f['ext']]
                    ]
                    
                    video_details = {
                        'title': info_dict.get('title'),
                        'thumbnail': info_dict.get('thumbnail'),
                        'formats': filtered_formats,
                        'url': url
                    }
                    
                    return render(request, 'ytdownloader/home.html', video_details)
            except Exception as e:
                logger.error(f"Error fetching video formats: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error fetching video formats: {e}"})
        
        if url and format_id:
            try:
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        percent = d['_percent_str']
                        # Strip ANSI escape codes
                        cleaned_percent = strip_ansi_codes(percent)
                        # Update the progress bar element in the HTML
                        progress = int(float(cleaned_percent.replace('%', '').strip()))
                        logger.debug(f"Download progress: {progress}%")
                        # Send progress update to the client
                        request.session['progress'] = progress
                    elif d['status'] == 'finished':
                        request.session['progress'] = 100
                    logger.debug(f"Progress hook called with status: {d['status']}")

                # Extract video info to get the title
                ydl_opts_info = {}
                with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    title = info_dict.get('title')
                    thumbnail = info_dict.get('thumbnail')
                    ext = 'mp4'  # Default extension
                    format_note = next((f['format_note'] for f in info_dict['formats'] if f['format_id'] == format_id), 'N/A')

                # Sanitize the title for the filename
                sanitized_title = sanitize_filename(title)
                logger.debug(f"Sanitized title: {sanitized_title}")

                # Create the filename with title, quality, and format
                filename = f"{sanitized_title}_{format_note}.{ext}"
                output_path = os.path.join(os.path.expanduser('~'), 'Downloads', filename)

                ydl_opts = {
                    'format': format_id,
                    'outtmpl': output_path,
                    'progress_hooks': [progress_hook]
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                logger.debug(f"File path: {output_path}")
                with open(output_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='video/mp4')
                    # Encode the filename for Content-Disposition header
                    encoded_filename = urllib.parse.quote(filename)
                    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
                    
                    # Save the download record to the database
                    YouTubeDownload.objects.create(
                        user=request.user,
                        url=url,
                        format_id=format_id,
                        title=title,
                        thumbnail=thumbnail  # Ensure this line is correct
                    )
                    
                    return response
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error downloading video: {e}"})
    
    # Fetch the user's downloads
    downloads = YouTubeDownload.objects.filter(user=request.user)
    mp3_format_ids = [download.format_id for download in downloads if 'mp3' in download.format_id]
    return render(request, 'ytdownloader/home.html', {'downloads': downloads, 'mp3_format_ids': mp3_format_ids})

@login_required
def get_progress(request):
    progress = request.session.get('progress', 0)
    logger.debug(f"Progress fetched: {progress}%")
    return JsonResponse({'progress': progress})