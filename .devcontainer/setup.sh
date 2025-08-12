#!/bin/bash

set -e

echo "🚀 Setting up vidaud development environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -y

# Install FFmpeg (required for video conversion)
echo "🎥 Installing FFmpeg..."
sudo apt-get install -y ffmpeg

# Install additional useful tools
echo "🛠️ Installing development tools..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    make \
    tree \
    htop \
    jq \
    nano \
    vim

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify FFmpeg installation
echo "✅ Verifying FFmpeg installation..."
ffmpeg -version | head -1

# Verify Python tools
echo "✅ Verifying Python tools..."
python --version
pip --version

# Run initial tests to verify setup
echo "🧪 Running quick setup verification..."
python -m pytest tests/test_converter.py::TestVideoConverter::test_metadata_extraction -v

echo "🎉 Development environment setup complete!"
echo ""
echo "Available commands:"
echo "  make help      - Show all available commands"
echo "  make test      - Run all tests"
echo "  make lint      - Check code quality"
echo "  make lint-fix  - Fix code formatting"
echo "  make security  - Run security checks"
echo "  make build     - Build Docker image"
echo "  make run       - Run with docker-compose"
echo ""
echo "Happy coding! 🚀"
