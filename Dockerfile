# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

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
