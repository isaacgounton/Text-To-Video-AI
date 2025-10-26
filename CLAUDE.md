# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Text-to-Video AI application that generates short videos from text prompts. The system creates engaging YouTube Shorts-style videos (under 50 seconds) by:

1. Generating a script from a topic using OpenAI/Groq
2. Converting text to speech using Edge TTS
3. Transcribing audio with Whisper to get timing
4. Finding relevant background videos from Pexels API
5. Rendering the final video with captions using MoviePy

## Environment Setup

### Required API Keys

Option 1: Environment Variables
```bash
export OPENAI_KEY="your-openai-api-key"
export PEXELS_KEY="your-pexels-api-key"
export GROQ_API_KEY="your-groq-api-key"  # Optional, uses OpenAI if not set
```

Option 2: Environment File (Recommended)
```bash
# Copy the example file and add your actual API keys
cp .env.example .env
# Edit .env with your actual keys
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

### Web Interface (Recommended)
```bash
streamlit run web_interface.py
```
Access the web interface at `http://localhost:8501`

### Command Line (Original)
```bash
python app.py "Your topic here"
```

The output will be saved as `rendered_video.mp4` in the root directory.

### Docker Deployment
```bash
# Using Docker Compose (Recommended for production)
# First create .env file with your API keys
cp .env.example .env
# Edit .env with your actual keys, then run:
docker-compose up

# Or using Docker directly
docker build -t text-to-video-ai .
docker run -p 8501:8501 --env-file .env text-to-video-ai
```

### Alternative: Google Colab
For quick testing without local setup, use the provided `Text_to_Video_example.ipynb` notebook.

## Architecture

### Core Pipeline (app.py:15-48)
The main application follows this sequence:

1. **Script Generation** - Uses AI to create ~140-word fact-based scripts
2. **Audio Generation** - Converts script to speech using Edge TTS
3. **Caption Timing** - Uses Whisper to get word-level timestamps
4. **Video Search** - Generates search queries and finds background videos
5. **Video Rendering** - Combines audio, captions, and background videos

### Key Components

#### Script Generator (utility/script/script_generator.py:16-61)
- Uses OpenAI GPT-4o or Groq Mixtral-8x7b model
- Generates concise, engaging facts-style scripts
- Returns structured JSON with script content
- Handles JSON parsing fallbacks

#### Audio Generator (utility/audio/audio_generator.py:3-5)
- Uses Edge TTS with Australian male voice (en-AU-WilliamNeural)
- Simple async function for TTS generation

#### Caption Generator (utility/captions/timed_captions_generator.py:5-71)
- Uses Whisper model for transcription and timing
- Splits captions by word count (max 15 characters per caption)
- Returns time-coded text segments for overlay

#### Video Search Query Generator (utility/video/video_search_query_generator.py:51-91)
- Analyzes script and captions to extract visual keywords
- Generates time-stamped search queries for background videos
- Ensures 2-4 second intervals with visual search terms

#### Background Video Generator (utility/video/background_video_generator.py:55-71)
- Integrates with Pexels API for video search
- Filters for 1920x1080 landscape videos
- Avoids duplicate video usage
- Currently supports Pexels, with placeholder for Stable Diffusion

#### Render Engine (utility/render/render_engine.py:32-78)
- Uses MoviePy for video composition
- Downloads background videos temporarily
- Combines audio, video clips, and text overlays
- Requires ImageMagick for text rendering

### Utility Functions

#### Logging (utility/utils.py:14-35)
- Logs API responses from OpenAI and Pexels
- Creates timestamped log files in `.logs/` directory
- Useful for debugging and cost tracking

## Configuration

### Model Selection
The system automatically chooses between:
- Groq Mixtral-8x7b for script generation (if GROQ_API_KEY is set)
- Groq Llama3-70b-8192 for video search queries (if GROQ_API_KEY is set)
- OpenAI GPT-4o as fallback for both functions

### Video Server Options
Currently only Pexels is implemented:
- Video server is set to "pexel" in app.py:22
- Alternative "stable_diffusion" option exists in code but is not implemented

### Output Settings
- Video format: MP4 with H.264 codec, AAC audio
- Resolution: 1920x1080 (16:9 aspect ratio)
- Frame rate: 25 FPS
- Text overlay: White text with black stroke, 100pt font
- Text position: Centered horizontally at y=800

## Key Files and Their Purposes

- `app.py` - Main orchestrator that runs complete pipeline (CLI version)
- `web_interface.py` - Streamlit web interface for user-friendly interaction
- `docker-compose.yml` - Docker Compose configuration for deployment
- `Dockerfile` - Docker container configuration
- `utility/script/script_generator.py` - AI-powered script creation
- `utility/audio/audio_generator.py` - Text-to-speech conversion
- `utility/captions/timed_captions_generator.py` - Audio transcription and timing
- `utility/video/video_search_query_generator.py` - Video search term extraction
- `utility/video/background_video_generator.py` - Pexels API integration
- `utility/render/render_engine.py` - Final video composition
- `utility/utils.py` - Shared utilities and logging

## Development Notes

### API Rate Limits
- Pexels API has rate limits; consider implementing delays for large projects
- Multiple API calls are made during video search (one per time segment)

### Performance Considerations
- Video downloading is synchronous and may be slow
- Whisper model loading happens on each caption generation call
- Temporary video files are created and deleted during rendering

### Error Handling
- JSON parsing includes fallback mechanisms for malformed AI responses
- Empty video search results are handled gracefully
- Missing ImageMagick path defaults to `/usr/bin/convert`

## Testing

### Web Interface Testing
1. Set up required API keys
2. Run `streamlit run web_interface.py`
3. Open `http://localhost:8501` in browser
4. Test with a simple topic like "space facts"
5. Check output in `rendered_video.mp4`

### Command Line Testing
1. Set up required API keys
2. Run `python app.py "space facts"`
3. Check output in `rendered_video.mp4`

### Docker Testing
1. Set up required API keys in environment or `.env` file
2. Run `docker-compose up`
3. Access `http://localhost:8501`
4. Test functionality through web interface

For all testing methods, review logs in `.logs/` for debugging information.