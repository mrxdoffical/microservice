from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import yt_dlp
import os
import re
import logging
import urllib.parse
import math
import subprocess
import time
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
        if 'fetch_formats' in request.POST:
            url = request.POST.get('url')
            logger.debug(f"Received URL: {url}")

            youtube_regex = re.compile(
                r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
            )
            if not youtube_regex.match(url):
                logger.error("Invalid YouTube URL")
                return render(request, 'ytdownloader/home.html', {'error': 'Invalid YouTube URL'})

            try:
                info_dict = extract_video_info(url)
                formats = info_dict.get('formats', [])
                duration = info_dict.get('duration', 0)

                # Filter for MP4 formats and prepare details
                video_formats = []
                for f in formats:
                    if f['ext'] == 'mp4':  # Only include MP4 formats
                        resolution = f.get('height', 'N/A')
                        quality = f.get('format_note', 'N/A')

                        # Exclude formats with 'N/A' resolution or quality
                        if resolution == 'N/A' or quality == 'N/A':
                            continue

                        filesize = f.get('filesize')
                        if not filesize and duration and f.get('tbr'):
                            filesize = (f['tbr'] * 1000 / 8) * duration  # Convert tbr from kbps to bytes per second

                        size = format_size(filesize) if filesize else 'Unknown'

                        # Append valid formats only
                        video_formats.append({
                            'format_id': f['format_id'],
                            'format_note': quality,
                            'ext': f['ext'],
                            'resolution': resolution,
                            'size': size,
                            'files': filesize
                        })

                # Sort formats by resolution (if available) in descending order
                video_formats = sorted(video_formats, key=lambda x: (x['resolution'] if x['resolution'] != 'N/A' else 0), reverse=True)

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

        elif 'download_video' in request.POST:
            url = request.POST.get('url')
            format_id = request.POST.get('format_id')
            logger.debug(f"Received URL: {url}")

            try:
                info_dict = extract_video_info(url)
                title = info_dict.get('title')
                thumbnail = info_dict.get('thumbnail')

                # Generate unique filenames using a timestamp
                timestamp = int(time.time())
                video_filename = f"{sanitize_filename(title)}_video_{timestamp}.mp4"
                audio_filename = f"{sanitize_filename(title)}_audio_{timestamp}.mp4"
                combined_filename = f"{sanitize_filename(title)}_combined_{timestamp}.mp4"

                video_output_path = os.path.join(os.path.expanduser('~'), 'Downloads', video_filename)
                audio_output_path = os.path.join(os.path.expanduser('~'), 'Downloads', audio_filename)
                combined_output_path = os.path.join(os.path.expanduser('~'), 'Downloads', combined_filename)

                # Determine format for video and audio
                video_format = next((f for f in info_dict['formats'] if f['format_id'] == format_id and 'video' in f.get('ext', '')), None)
                audio_format = next((f for f in info_dict['formats'] if 'audio' in f.get('ext', '') and f.get('height') == 360), None)

                # Handle combining video and audio if both formats are available
                if video_format and audio_format:
                    ydl_opts_video = {
                        'format': video_format['format_id'],
                        'outtmpl': video_output_path,
                        'noplaylist': True,
                        'nooverwrites': True
                    }

                    ydl_opts_audio = {
                        'format': audio_format['format_id'],
                        'outtmpl': audio_output_path,
                        'noplaylist': True,
                        'nooverwrites': True
                    }

                    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                        ydl.download([url])

                    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                        ydl.download([url])

                    # Combine video and audio using ffmpeg
                    combine_command = [
                        'ffmpeg',
                        '-i', video_output_path,
                        '-i', audio_output_path,
                        '-c:v', 'libx264',         # Use libx264 codec for video
                        '-c:a', 'aac',             # Use AAC codec for audio
                        '-strict', 'experimental', # Allow experimental codecs (AAC)
                        '-map', '0:v:0',           # Map video from the first input
                        '-map', '1:a:0',           # Map audio from the second input
                        '-b:a', '192k',            # Set audio bitrate to 192 kbps (might be better for compatibility)
                        '-movflags', 'faststart',  # Optimize for web and streaming compatibility
                        combined_output_path
                    ]

                    subprocess.run(combine_command, check=True)

                    # Clean up temporary files
                    os.remove(video_output_path)
                    os.remove(audio_output_path)

                else:
                    # Single MP4 format case
                    ydl_opts = {
                        'format': format_id,
                        'outtmpl': combined_output_path,
                        'noplaylist': True,
                        'nooverwrites': True
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                logger.debug(f"File path: {combined_output_path}")
                with open(combined_output_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='video/mp4')
                    encoded_filename = urllib.parse.quote(combined_filename)
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

def search_youtube(request):
    query = request.GET.get('query')
    if query:
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch10',
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(query, download=False)
                results = info_dict.get('entries', [])
                return render(request, 'ytdownloader/search_results.html', {'results': results})
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return render(request, 'ytdownloader/search_results.html', {'error': str(e)})
    return redirect('home')