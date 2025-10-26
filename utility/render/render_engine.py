import time
import os
import tempfile
import zipfile
import platform
import subprocess
try:
    from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                                TextClip, VideoFileClip)
except ImportError:
    from moviepy import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                      TextClip, VideoFileClip)
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.audio_normalize import audio_normalize
import requests
import streamlit as st

def download_file(url, filename):
    with open(filename, 'wb') as f:
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        f.write(response.content)

def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        result = subprocess.check_output([search_cmd, program_name]).decode().strip()
        return result if result else None
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    """Try multiple methods to find a program"""
    # Method 1: Use 'which' or 'where' command
    program_path = search_program(program_name)
    if program_path:
        return program_path
    
    # Method 2: Common paths for ImageMagick on Linux
    if program_name == "magick":
        common_paths = [
            "/usr/bin/magick",
            "/usr/bin/convert",
            "/usr/local/bin/magick",
            "/usr/local/bin/convert",
        ]
        for path in common_paths:
            if os.path.exists(path):
                print(f"Found {program_name} at: {path}")
                return path
    
    return None

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    
    # Try to detect ImageMagick binary
    magick_path = get_program_path("magick")
    
    # If magick not found, try convert command
    if not magick_path:
        magick_path = get_program_path("convert")
    
    print(f"ImageMagick path detected: {magick_path}")
    
    # Try to use streamlit if available, otherwise just print
    try:
        if magick_path:
            st.info(f"✅ ImageMagick found at: {magick_path}")
            os.environ['IMAGEMAGICK_BINARY'] = magick_path
        else:
            st.warning(f"⚠️ ImageMagick not found, attempting to use system default...")
            st.info("💡 If you see text rendering errors, install ImageMagick: sudo apt install imagemagick")
            # Set fallback paths
            os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'
    except NameError:
        # Streamlit not available (running outside of Streamlit)
        if magick_path:
            os.environ['IMAGEMAGICK_BINARY'] = magick_path
        else:
            os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'
    
    # Check if audio file exists
    if not audio_file_path or not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"No audio was received. Audio file not found at: {audio_file_path}")
    
    # Store temporary video filenames for cleanup
    downloaded_video_files = []
    visual_clips = []
    
    for (t1, t2), video_url in background_video_data:
        # Download the video file
        video_filename = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        download_file(video_url, video_filename)
        downloaded_video_files.append(video_filename)
        
        # Create VideoFileClip from the downloaded file
        video_clip = VideoFileClip(video_filename)
        video_clip = video_clip.set_start(t1)
        video_clip = video_clip.set_end(t2)
        visual_clips.append(video_clip)
    
    audio_clips = []
    audio_file_clip = AudioFileClip(audio_file_path)
    audio_clips.append(audio_file_clip)

    for (t1, t2), text in timed_captions:
        text_clip = TextClip(txt=text, fontsize=100, color="white", stroke_width=3, stroke_color="black", method="label")
        text_clip = text_clip.set_start(t1)
        text_clip = text_clip.set_end(t2)
        text_clip = text_clip.set_position(["center", 800])
        visual_clips.append(text_clip)

    video = CompositeVideoClip(visual_clips)
    
    if audio_clips:
        audio = CompositeAudioClip(audio_clips)
        video.duration = audio.duration
        video.audio = audio

    video.write_videofile(OUTPUT_FILE_NAME, codec='libx264', audio_codec='aac', fps=25, preset='veryfast')
    
    # Clean up downloaded video files
    for video_filename in downloaded_video_files:
        try:
            if os.path.exists(video_filename):
                os.remove(video_filename)
        except Exception as e:
            print(f"Warning: Could not delete temporary file {video_filename}: {e}")

    return OUTPUT_FILE_NAME
