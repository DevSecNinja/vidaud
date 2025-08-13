# vidaud - Video to Audio Converter

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap, Build, and Test Process
- **Install system dependencies (REQUIRED):**
  - `sudo apt-get update && sudo apt-get install -y ffmpeg` -- takes 3 minutes. NEVER CANCEL. Set timeout to 5+ minutes.
- **Setup repository:**
  - `./setup.sh` -- takes <1 second
  - `make deps` -- takes 60 seconds. NEVER CANCEL. Set timeout to 90+ seconds.
- **Test the codebase:**
  - `make test-unit` -- takes 8 seconds. Fast unit tests only.
  - `make test` -- takes 8 seconds. Full test suite (integration tests skipped if no network).
  - All 13 unit tests pass consistently. 4 integration tests are skipped without network access.
- **Code quality checks:**
  - `make lint` -- takes 1 second. Runs flake8 and black formatting check.
  - `make security` -- takes 5 seconds. Runs bandit security scanner.

### Run the Application
- **Development mode (RECOMMENDED):**
  ```bash
  # Set environment variables explicitly (required)
  INPUT_DIR=./test_input OUTPUT_DIR=./test_output PYTHONPATH=. python main.py
  ```
  - The .env file is NOT automatically loaded - you MUST set environment variables explicitly
  - Application starts immediately and monitors ./test_input for video files
  - Health endpoint available at http://localhost:8080/health

- **Docker mode:**
  - `make build` -- **FAILS in sandboxed environments due to SSL certificate issues**
  - `make run` -- depends on successful build, will fail in environments with network restrictions
  - Use development mode instead when Docker build fails

### Validation Scenarios
- **ALWAYS test video conversion after making changes:**
  1. Start the application in development mode with proper environment variables
  2. Create a test video: `ffmpeg -f lavfi -i testsrc=duration=5:size=320x240:rate=1 -f lavfi -i sine=frequency=1000:duration=5 -c:v libx264 -c:a aac -shortest test_input/sample.mp4 -y`
  3. Verify conversion appears in test_output/ as MP3 within 30 seconds
  4. Check health endpoint: `make health` or `curl http://localhost:8080/health`
- **ALWAYS test that directory monitoring works:**
  1. With application running, add another video file to test_input/
  2. Verify automatic detection and conversion to test_output/
- **ALWAYS run linting before committing:** `make lint` and `make security`

## Known Limitations and Workarounds

### Docker Build Issues
- **Problem:** `make build` fails with SSL certificate verification errors in sandboxed environments
- **Workaround:** Use development mode instead: `INPUT_DIR=./test_input OUTPUT_DIR=./test_output PYTHONPATH=. python main.py`
- **Note:** This is a known limitation of network-restricted environments, not a code issue

### Environment Configuration
- **Problem:** `make dev` fails because .env file is not automatically loaded
- **Workaround:** Set environment variables explicitly when running Python directly
- **Required variables:** `INPUT_DIR`, `OUTPUT_DIR`, `PYTHONPATH=.`

### Integration Tests
- **Problem:** Integration tests are skipped due to network access requirements
- **Expected:** Tests download sample files from samples.ffmpeg.org
- **Workaround:** Unit tests provide sufficient coverage for development

### Directory Permissions
- **Problem:** Permission denied errors for test directories
- **Fix:** Run `sudo chown -R $(whoami):$(id -gn) test_input test_output` to fix ownership

## Common Tasks

### Make All Tests Pass
```bash
# Install dependencies if not done
sudo apt-get update && sudo apt-get install -y ffmpeg  # 3 min timeout
make deps  # 90 sec timeout

# Run tests
make test  # 8 seconds, all unit tests should pass

# Code quality
make lint  # 1 second
make security  # 5 seconds
```

### Test Video Conversion Functionality
```bash
# Start application (in separate terminal/session)
INPUT_DIR=./test_input OUTPUT_DIR=./test_output PYTHONPATH=. python main.py

# Create test video
ffmpeg -f lavfi -i testsrc=duration=5:size=320x240:rate=1 -f lavfi -i sine=frequency=1000:duration=5 -c:v libx264 -c:a aac -shortest test_input/sample.mp4 -y

# Verify conversion (should appear in test_output/ within 30 seconds)
ls -la test_output/
file test_output/sample.mp3

# Test health endpoint
make health
# Should show: ✅ Status: healthy
```

### Debug Application Issues
```bash
# Run with debug logging
LOG_LEVEL=DEBUG INPUT_DIR=./test_input OUTPUT_DIR=./test_output PYTHONPATH=. python main.py

# Check health and metrics
curl http://localhost:8080/health | python3 -m json.tool
curl http://localhost:8080/metrics | python3 -m json.tool
```

## Repository Structure

### Key Files and Directories
```
vidaud/
├── src/                    # Main application code
│   ├── config.py          # Configuration management (environment variables)
│   ├── converter.py       # FFmpeg video-to-audio conversion logic
│   ├── monitor.py         # File monitoring with Linux inotify
│   └── health_server.py   # FastAPI health check endpoints
├── tests/                 # Test suite (13 unit tests, 4 integration tests)
├── test_input/            # Input directory for development (created by setup.sh)
├── test_output/           # Output directory for development (created by setup.sh)
├── main.py               # Application entry point
├── Makefile              # Development commands
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker configuration
└── .env                  # Environment configuration (NOT auto-loaded)
```

### Frequently Used Commands (from Makefile)
```bash
make help          # Show all available commands
make setup         # Initial project setup (fast)
make deps          # Install dependencies (60s timeout)
make test          # Run test suite (8s)
make test-unit     # Unit tests only (8s)
make lint          # Code quality checks (1s)
make security      # Security scanning (5s)
make health        # Check running application health
make clean         # Clean up Docker resources
```

## Configuration Reference

### Environment Variables (Required for Development)
- `INPUT_DIR=./test_input` -- Directory to monitor for video files
- `OUTPUT_DIR=./test_output` -- Directory for converted audio files
- `PYTHONPATH=.` -- Required for Python module imports
- `LOG_LEVEL=INFO` -- Optional: DEBUG for verbose logging
- `OUTPUT_FORMAT=mp3` -- Optional: mp3 or flac
- `MAX_PARALLEL_JOBS=4` -- Optional: Concurrent conversion jobs

### Supported Video Formats
- **Input:** MKV, WebM, MP4, AVI, MOV, WMV
- **Output:** MP3 (320kbps, 44.1kHz) or FLAC (lossless)

### Health Endpoints
- `http://localhost:8080/health` -- Application health status
- `http://localhost:8080/metrics` -- Processing metrics and statistics

## CI/CD Pipeline (.github/workflows/ci.yml)

The automated pipeline runs:
1. **Tests** on Python 3.11 and 3.12 (unit + integration)
2. **Quality checks** (flake8, black, bandit security scan)
3. **Docker build** for AMD64 and ARM64 architectures
4. **Release** automation with GitHub releases

### Workflow triggers:
- Push to `main` or `feature/*` branches
- Pull requests to `main`
- Version tags (`v*`) trigger releases