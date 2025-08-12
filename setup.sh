#!/bin/bash

# Simple setup script for vidaud

set -e

echo "🎵 Setting up vidaud - Video to Audio Converter"
echo "================================================"

# Create directories if they don't exist
echo "Creating input and output directories..."
mkdir -p ./test_input ./test_output

# Copy example environment file
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it to match your setup."
else
    echo "✓ .env file already exists."
fi

# Set permissions for Docker container (UID 1000)
echo "Setting directory permissions..."
chown -R 1000:1000 ./test_input ./test_output 2>/dev/null || sudo chown -R 1000:1000 ./test_input ./test_output || echo "Note: Could not set ownership. You may need to run: sudo chown -R 1000:1000 ./test_input ./test_output"

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env file to configure your settings"
echo "2. Place video files in ./test_input directory"
echo "3. Run: docker-compose up -d"
echo "4. Check logs: docker-compose logs -f"
echo "5. Health check: curl http://localhost:8080/health"
echo ""
echo "Converted audio files will appear in ./test_output directory"
