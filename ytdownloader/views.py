from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import yt_dlp
import os
import re
import logging
import urllib.parse
import math
from .models import YouTubeDownload

logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename

def extract_video_info(url):
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
    return info_dict

def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@login_required
def home(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        format_id = request.POST.get('format_id')
        logger.debug(f"Received URL: {url}")
        
        youtube_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
        )
        if not youtube_regex.match(url):
            logger.error("Invalid YouTube URL")
            return render(request, 'ytdownloader/home.html', {'error': 'Invalid YouTube URL'})
        
        if url and not format_id:
            try:
                info_dict = extract_video_info(url)
                formats = info_dict.get('formats', [])
                duration = info_dict.get('duration', 0)
                
                # Group formats by resolution and select the best format for each resolution
                best_formats = {}
                for f in formats:
                    if f['ext'] == 'mp4' and f.get('acodec') != 'none':  # Ensure the format has an audio track
                        resolution = f.get('resolution') or f.get('height')
                        tbr = f.get('tbr')
                        if resolution and tbr is not None:
                            if resolution not in best_formats or tbr > best_formats[resolution].get('tbr', 0):
                                best_formats[resolution] = f
                
                video_formats = []
                for f in best_formats.values():
                    resolution = f.get('resolution') or f.get('height', 'N/A')
                    if resolution != 'N/A' and 'x' in resolution:
                        quality = resolution.split('x')[1]
                    else:
                        quality = 'N/A'
                    
                    filesize = f.get('filesize')
                    if not filesize and duration and f.get('tbr'):
                        filesize = (f['tbr'] * 1000 / 8) * duration  # Convert tbr from kbps to bytes per second
                    
                    size = format_size(filesize) if filesize else 'Unknown'
                    
                    video_formats.append({
                        'format_id': f['format_id'],
                        'format_note': f.get('format_note', quality),
                        'ext': f['ext'],
                        'resolution': resolution,
                        'size': size,
                        'filesize': filesize
                    })
                
                video_details = {
                    'title': info_dict.get('title'),
                    'thumbnail': info_dict.get('thumbnail'),
                    'video_formats': video_formats,
                    'url': url
                }
                
                return render(request, 'ytdownloader/home.html', video_details)
            except Exception as e:
                logger.error(f"Error fetching video formats: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error fetching video formats: {e}"})
        
        if url and format_id:
            try:
                info_dict = extract_video_info(url)
                title = info_dict.get('title')
                thumbnail = info_dict.get('thumbnail')
                format_note = next((f.get('format_note', 'N/A') for f in info_dict['formats'] if f['format_id'] == format_id), 'N/A')

                sanitized_title = sanitize_filename(title)
                logger.debug(f"Sanitized title: {sanitized_title}")

                filename = f"{sanitized_title}_{format_note}.mp4"
                output_path = os.path.join(os.path.expanduser('~'), 'Downloads', filename)

                ydl_opts = {
                    'format': format_id,
                    'outtmpl': output_path
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                logger.debug(f"File path: {output_path}")
                with open(output_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='video/mp4')
                    encoded_filename = urllib.parse.quote(filename)
                    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
                    
                    YouTubeDownload.objects.create(
                        user=request.user,
                        url=url,
                        format_id=format_id,
                        title=title,
                        thumbnail=thumbnail
                    )
                    
                    return response
            except Exception as e:
                logger.error(f"Error downloading video: {e}")
                return render(request, 'ytdownloader/home.html', {'error': f"Error downloading video: {e}"})
    
    downloads = YouTubeDownload.objects.filter(user=request.user)
    return render(request, 'ytdownloader/home.html', {'downloads': downloads})