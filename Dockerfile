# Use Python 3.11 slim as base image
FROM python:3.11-slim

# Install system dependencies required for the application
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and output
RUN mkdir -p .logs/gpt_logs .logs/pexel_logs

# Set environment variables for MoviePy and ImageMagick
ENV IMAGEMAGICK_BINARY=/usr/bin/convert
ENV MOVIEPY_TEMP_DIR=/tmp/moviepy

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (if needed for future web interface)
EXPOSE 8000

# Default command
CMD ["python", "app.py", "AI and technology facts"]