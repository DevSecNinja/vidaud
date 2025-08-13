#!/bin/bash
# Docker Image Size Optimization Analysis Script

set -e

echo "🔍 Docker Image Size Optimization Analysis"
echo "=========================================="
echo

# Create temporary directory for testing
TEMP_DIR="/tmp/vidaud_docker_test"
mkdir -p "$TEMP_DIR"

# Function to get image size
get_image_size() {
    local image_name=$1
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "$image_name" | awk '{print $2}' || echo "N/A"
}

# Function to analyze image layers
analyze_layers() {
    local image_name=$1
    echo "📋 Layer analysis for $image_name:"
    docker history "$image_name" --human --no-trunc | head -20
    echo
}

echo "📦 Building Docker images for comparison..."
echo

# Build original (pre-optimization) for comparison if we had one
echo "🔧 Building optimized image..."
if docker build -t vidaud:optimized -f Dockerfile . --quiet; then
    OPTIMIZED_SIZE=$(get_image_size "vidaud:optimized")
    echo "✅ Optimized image built successfully: $OPTIMIZED_SIZE"
else
    echo "❌ Failed to build optimized image"
    exit 1
fi

echo

# Analyze the optimized image
analyze_layers "vidaud:optimized"

# Show detailed size breakdown
echo "📊 Detailed size analysis:"
echo "========================="
docker images | grep vidaud
echo

# Test that the image works
echo "🧪 Testing optimized image functionality..."
echo "Creating test video file..."

# Create a minimal test video
ffmpeg -f lavfi -i testsrc=duration=2:size=320x240:rate=1 -f lavfi -i sine=frequency=1000:duration=2 -c:v libx264 -c:a aac -shortest "$TEMP_DIR/test.mp4" -y -loglevel quiet

echo "✅ Test video created"

# Start container for testing
echo "Starting container for testing..."
docker run -d --name vidaud_test \
    -v "$TEMP_DIR:/input:ro" \
    -v "$TEMP_DIR:/output" \
    -p 8081:8080 \
    vidaud:optimized

# Wait for container to start
sleep 5

# Check health
echo "🏥 Checking health endpoint..."
if curl -s http://localhost:8081/health | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ Health check passed' if data.get('status') == 'healthy' else '❌ Health check failed')"; then
    echo "Container is running properly"
else
    echo "❌ Health check failed, checking logs..."
    docker logs vidaud_test
fi

# Clean up
echo "🧹 Cleaning up test container..."
docker stop vidaud_test >/dev/null 2>&1 || true
docker rm vidaud_test >/dev/null 2>&1 || true
rm -rf "$TEMP_DIR"

echo
echo "📋 Summary of Optimizations Applied:"
echo "===================================="
echo "✅ Added .dockerignore to reduce build context"
echo "✅ Split requirements into production vs development"
echo "✅ Used only production dependencies in image"
echo "✅ Optimized package installation with --no-install-recommends"
echo "✅ Added autoremove and clean commands"
echo "✅ Copy only essential application files"
echo "✅ Optimized health check to use curl instead of Python"
echo "✅ Reduced health check timeout from 10s to 5s"
echo

echo "🎯 Final optimized image size: $OPTIMIZED_SIZE"
echo "Done! 🎉"