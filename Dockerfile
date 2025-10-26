FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set ImageMagick policy to allow PDF and other formats
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/g' /etc/ImageMagick-6/policy.xml

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Streamlit
RUN pip install streamlit

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p .logs/gpt_logs .logs/pexel_logs

# Create uploads directory for temporary files
RUN mkdir -p uploads

# Expose port for Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Run Streamlit app
CMD ["streamlit", "run", "web_interface.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]