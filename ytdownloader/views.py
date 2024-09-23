from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import yt_dlp
import os
import re
import logging
import time
import urllib.parse
import math
import subprocess
from django.http import HttpResponse

logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """Sanitize the filename to remove invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def extract_video_info(url):
    """Extract video information without downloading."""
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
    return info_dict

def format_size(size_bytes):
    """Convert bytes to a human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def combine_video_audio(video_path, audio_path, output_path):
    """Combine video and audio tracks using ffmpeg."""
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path}")
            return False
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            return False

        command = [
            'ffmpeg', '-y', '-i', video_path, '-i', audio_path,
            '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_path
        ]
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error combining video and audio: {e}")
        return False

def download_audio_format(url, best_audio_format, title, timestamp):
    """Download the best audio format available as MP3."""
    audio_filename = f"{sanitize_filename(title)}_audio_{timestamp}"
    audio_path = os.path.join(os.path.expanduser('~'), 'Downloads', audio_filename)

    ydl_opts_audio = {
        'format': best_audio_format['format_id'],
        'outtmpl': audio_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'keepvideo': False,
        'keepaudio': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    return audio_path+".mp3"

@login_required
def home(request):
    """View for fetching video formats and downloading the selected one."""
    if request.method == 'POST':
        if 'fetch_formats' in request.POST:
            url = request.POST.get('url')

            youtube_regex = re.compile(
                r'^(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+$'
            )
            if not youtube_regex.match(url):
                return render(request, 'ytdownloader/home.html', {'error': 'Invalid YouTube URL'})

            try:
                info_dict = extract_video_info(url)
                formats = info_dict.get('formats', [])
                title = info_dict.get('title', 'No Title')
                thumbnail = info_dict.get('thumbnail', '')
                duration = info_dict.get('duration', 0)

                best_formats = {}
                audio_formats = []

                for f in formats:
                    resolution = f.get('height', 'N/A')
                    filesize = f.get('filesize')

                    if not filesize and duration and f.get('tbr'):
                        filesize = (f['tbr'] * 1000 / 8) * duration

                    size = format_size(filesize) if filesize else 'Unknown'

                    if f.get('acodec', 'none') != 'none':
                        audio_formats.append({
                            'format_id': f['format_id'],
                            'tbr': f.get('tbr', 0) or 0,
                            'ext': f.get('ext', 'unknown'),
                        })

                    if f['ext'] == 'mp4':
                        if resolution not in best_formats or (best_formats[resolution]['tbr'] or 0) < (f.get('tbr', 0) or 0):
                            best_formats[resolution] = {
                                'format_id': f['format_id'],
                                'format_note': f.get('format_note', 'N/A'),
                                'ext': f['ext'],
                                'resolution': resolution,
                                'size': size,
                                'acodec': f.get('acodec', 'none'),
                                'tbr': f.get('tbr', 0) or 0,
                            }

                video_formats = list(best_formats.values())

                context = {
                    'title': title,
                    'thumbnail': thumbnail,
                    'video_formats': video_formats,
                    'url': url,
                }
                request.session['audio_formats'] = audio_formats
                return render(request, 'ytdownloader/home.html', context)

            except Exception as e:
                return render(request, 'ytdownloader/home.html', {'error': f"Error fetching video formats: {e}"})

        elif 'download_video' in request.POST:
            url = request.POST.get('url')
            format_id = request.POST.get('format_id')
            download_type = request.POST.get('download_type')

            try:
                info_dict = extract_video_info(url)
                title = info_dict.get('title')
                timestamp = int(time.time())

                video_format = next((f for f in info_dict['formats'] if f['format_id'] == format_id), None)

                if download_type == 'audio':
                    audio_formats = request.session.get('audio_formats', [])
                    if audio_formats:
                        best_audio_format = max(audio_formats, key=lambda af: af['tbr'])
                        audio_path = download_audio_format(url, best_audio_format, title, timestamp)

                        response = HttpResponse(open(audio_path, 'rb'), content_type="audio/mpeg")
                        response['Content-Disposition'] = f'attachment; filename={urllib.parse.quote(os.path.basename(audio_path))}'
                        return response
                    else:
                        return render(request, 'ytdownloader/home.html', {'error': 'No audio format found.'})

                else:
                    # Only download once if video has both audio and video
                    if video_format and video_format.get('acodec', 'none') != 'none':
                        video_filename = f"{sanitize_filename(title)}_video_{timestamp}.mp4"
                        video_path = os.path.join(os.path.expanduser('~'), 'Downloads', video_filename)

                        ydl_opts_video = {
                            'format': format_id,
                            'outtmpl': video_path,
                            'noplaylist': True,
                        }
                        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                            ydl.download([url])

                        response = HttpResponse(open(video_path, 'rb'), content_type='video/mp4')
                        response['Content-Disposition'] = f'attachment; filename={urllib.parse.quote(video_filename)}'
                        return response

                    # If video lacks an audio track, download and combine audio
                    else:
                        video_filename = f"{sanitize_filename(title)}_video_{timestamp}.mp4"
                        video_path = os.path.join(os.path.expanduser('~'), 'Downloads', video_filename)

                        ydl_opts_video = {
                            'format': format_id,
                            'outtmpl': video_path,
                            'noplaylist': True,
                        }
                        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                            ydl.download([url])

                        audio_formats = request.session.get('audio_formats', [])
                        if audio_formats:
                            best_audio_format = max(audio_formats, key=lambda af: af['tbr'])
                            audio_path = download_audio_format(url, best_audio_format, title, timestamp)

                            combined_filename = f"{sanitize_filename(title)}_combined_{timestamp}.mp4"
                            combined_path = os.path.join(os.path.expanduser('~'), 'Downloads', combined_filename)
                            combine_success = combine_video_audio(video_path, audio_path, combined_path)

                            if combine_success:
                                response = HttpResponse(open(combined_path, 'rb'), content_type='video/mp4')
                                response['Content-Disposition'] = f'attachment; filename={urllib.parse.quote(combined_filename)}'
                                return response
                            else:
                                return render(request, 'ytdownloader/home.html', {'error': 'Error combining video and audio.'})

            except Exception as e:
                return render(request, 'ytdownloader/home.html', {'error': f"Error downloading video: {e}"})

    return render(request, 'ytdownloader/home.html')
