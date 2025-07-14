# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variables
export OPENAI_KEY="your-openai-api-key"
export PEXELS_KEY="your-pexels-api-key"

# Optional: Set Groq API key for alternative LLM
export GROQ_API_KEY="your-groq-api-key"
```

### Running the Application
```bash
# Generate video from text topic
python app.py "Topic name"

# Output will be generated as rendered_video.mp4
```

### Docker Development
```bash
# Copy environment variables template
cp .env.example .env
# Edit .env file with your API keys

# Build and run with Docker Compose
docker-compose up --build

# Run with custom topic
docker-compose run text-to-video-ai python app.py "Your custom topic"

# Build Docker image manually
docker build -t text-to-video-ai .

# Run Docker container manually
docker run -it --env-file .env -v $(pwd)/output:/app/output text-to-video-ai python app.py "Your topic"
```

### Alternative Development
- Use the Jupyter notebook `Text_to_Video_example.ipynb` for interactive development
- All cells can be run sequentially after setting up API keys

## Architecture Overview

This is a text-to-video AI application that generates short-form videos (YouTube Shorts style) from text topics.

### Core Pipeline (app.py)
1. **Script Generation** - Uses OpenAI/Groq to create YouTube Shorts scripts from topics
2. **Audio Generation** - Converts scripts to speech using edge-tts
3. **Caption Timing** - Uses Whisper to generate timed captions from audio
4. **Video Search** - Generates search queries and finds background videos from Pexels
5. **Video Rendering** - Combines audio, captions, and background videos using MoviePy

### Module Structure
- `utility/script/` - Script generation using OpenAI/Groq APIs
- `utility/audio/` - Text-to-speech conversion with edge-tts
- `utility/captions/` - Timed caption generation using Whisper
- `utility/video/` - Background video search and query generation
- `utility/render/` - Final video composition with MoviePy
- `utility/utils.py` - Logging utilities for API responses

### Key Dependencies
- **OpenAI/Groq** - Script generation (supports both APIs)
- **edge-tts** - Text-to-speech synthesis
- **whisper-timestamped** - Audio transcription with timing
- **MoviePy** - Video editing and composition
- **Pexels API** - Background video sourcing

### API Key Management
The application supports dual LLM providers:
- If `GROQ_API_KEY` is set (>30 chars), uses Groq with mixtral-8x7b-32768
- Otherwise uses OpenAI with gpt-4o model

### Output
- Final video: `rendered_video.mp4` (1920x1080, landscape orientation)
- Audio file: `audio_tts.wav`
- Logs stored in `.logs/` directory for debugging API responses