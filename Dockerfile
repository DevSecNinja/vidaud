# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

# Set build-time labels for org.opencontainers specification
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.opencontainers.image.title="vidaud - Video to Audio Converter"
LABEL org.opencontainers.image.description="A Docker-based application that automatically converts video files to audio formats (MP3/FLAC) while preserving metadata and folder structure for Plex compatibility."
LABEL org.opencontainers.image.authors="DevSecNinja"
LABEL org.opencontainers.image.vendor="DevSecNinja"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://github.com/DevSecNinja/vidaud"
LABEL org.opencontainers.image.source="https://github.com/DevSecNinja/vidaud"
LABEL org.opencontainers.image.documentation="https://github.com/DevSecNinja/vidaud/blob/main/README.md"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Inherit build-time arguments for labels
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set final image labels for org.opencontainers specification
LABEL org.opencontainers.image.title="vidaud - Video to Audio Converter"
LABEL org.opencontainers.image.description="A Docker-based application that automatically converts video files to audio formats (MP3/FLAC) while preserving metadata and folder structure for Plex compatibility."
LABEL org.opencontainers.image.authors="DevSecNinja"
LABEL org.opencontainers.image.vendor="DevSecNinja"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.url="https://github.com/DevSecNinja/vidaud"
LABEL org.opencontainers.image.source="https://github.com/DevSecNinja/vidaud"
LABEL org.opencontainers.image.documentation="https://github.com/DevSecNinja/vidaud/blob/main/README.md"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.version="${VERSION}"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security (NF5)
RUN groupadd -r vidaud && useradd -r -g vidaud -u 1000 vidaud

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=vidaud:vidaud . .

# Create directories for volumes
RUN mkdir -p /input /output && chown -R vidaud:vidaud /input /output

# Switch to non-root user
USER vidaud

# Health check endpoint (NF12)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Expose health endpoint port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
