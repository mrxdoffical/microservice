from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import VideoFileForm
from .models import VideoFile
from django.http import FileResponse
import os
from moviepy.editor import VideoFileClip

def upload_video(request):
    if request.method == 'POST':
        form = VideoFileForm(request.POST, request.FILES)
        if form.is_valid():
            video_file = form.save()
            success, message, audio_path = convert_mp4_to_mp3(video_file)
            if success:
                messages.success(request, message)
                return render(request, 'file_converter/upload_video.html', {'form': form, 'audio_path': audio_path})
            else:
                messages.error(request, message)
                return redirect('file_converter:upload_video')
    else:
        form = VideoFileForm()
    return render(request, 'file_converter/upload_video.html', {'form': form})

def download_file(request, file_path):
    file_path = os.path.join('media', 'converted', file_path)
    return FileResponse(open(file_path, 'rb'), as_attachment=True)

def convert_mp4_to_mp3(video_file):
    video_path = video_file.video.path
    audio_dir = os.path.join('media', 'converted')
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, os.path.splitext(os.path.basename(video_path))[0] + '.mp3')
    try:
        video_clip = VideoFileClip(video_path)
        if video_clip.audio is None:
            raise ValueError("No audio track found in the video file.")
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_path)
        audio_clip.close()
        video_clip.close()
        video_file.converted_audio = audio_path
        video_file.save()
        return True, f"Successfully converted {video_path} to {audio_path}", os.path.basename(audio_path)
    except ValueError as ve:
        return False, str(ve), None
    except Exception as e:
        return False, f"Error converting {video_path} to MP3: {e}", None