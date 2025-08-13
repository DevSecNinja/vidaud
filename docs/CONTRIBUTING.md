# Contributing to vidaud

This guide contains information for developers and contributors working on the vidaud project.

## Development Setup

### Prerequisites

- Python 3.11 or 3.12
- FFmpeg
- Docker (for containerized development)

### Local Development

#### Option 1: Using DevContainer (Recommended)

1. Open the project in VS Code
2. When prompted, click "Reopen in Container"
3. The devcontainer will automatically:
   - Install Python 3.12 and FFmpeg
   - Install all dependencies
   - Configure development tools
   - Run setup verification

#### Option 2: Manual Setup

```bash
# Clone repository
git clone https://github.com/devsecninja/vidaud.git
cd vidaud

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install ffmpeg

# Install Python dependencies
pip install -r requirements.txt

# Verify setup
make test
```

## Development Workflow

### Available Commands

```bash
make help          # Show all available commands
make test          # Run all tests
make test-unit     # Run only unit tests (no network required)
make test-integration  # Run integration tests (requires network)
make lint          # Check code quality
make lint-fix      # Fix code formatting automatically
make security      # Run security checks
make build         # Build Docker image
make run           # Run with docker-compose
make stop          # Stop docker-compose
make clean         # Clean up Docker resources
```

### Code Quality

The project uses standardized configuration files for consistent code quality:

- **`.flake8`**: Linting rules (line length 88, Black compatibility)
- **`pyproject.toml`**: Configuration for Black, pytest, Bandit, and coverage
- **Automatic formatting**: Run `make lint-fix` to auto-format code
- **Pre-commit checks**: All tools use shared configuration files

See [docs/CODE-QUALITY.md](CODE-QUALITY.md) for detailed information.

## Testing

### Test Structure

- **Unit Tests**: Fast tests that don't require network access
- **Integration Tests**: Test with real FFmpeg sample files from [samples.ffmpeg.org](https://samples.ffmpeg.org/)
- **Docker Tests**: Verify container functionality

### Running Tests

```bash
# Run all tests
make test

# Run only fast unit tests
make test-unit

# Run integration tests (downloads real video samples)
make test-integration

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Results

All 17 tests pass successfully:
- ✅ Unit tests: Configuration, conversion logic, monitoring
- ✅ Integration tests: Real video file conversion with FFmpeg samples
- ✅ Docker tests: Container functionality and health checks

## Docker Development

### Building Images

```bash
# Build standard image
make build

# Build multi-architecture image
docker buildx build --platform linux/amd64,linux/arm64 -t vidaud:latest .

# Test image locally
docker run --rm -it vidaud:latest python -c "import src.config; print('OK')"
```

### Docker Compose Development

```bash
# Start development environment
make run

# View logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8080/health

# Stop environment
make stop
```

## Project Structure

```
vidaud/
├── src/                    # Main application code
│   ├── config.py          # Configuration management
│   ├── converter.py       # Video-to-audio conversion logic
│   ├── monitor.py         # File monitoring with inotify
│   └── health_server.py   # Health check API
├── tests/                 # Test suite
│   ├── test_converter.py  # Unit tests for conversion
│   ├── test_monitor.py    # Unit tests for monitoring
│   └── test_integration.py # Integration tests with real files
├── docs/                  # Documentation
├── .devcontainer/         # VS Code development container
├── .github/workflows/     # CI/CD pipeline
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Container definition
├── Makefile              # Development commands
└── requirements.txt      # Python dependencies
```

## CI/CD Pipeline

The project uses GitHub Actions for automated testing and deployment:

- **Testing**: Runs on Python 3.11 and 3.12
- **Quality Checks**: Linting, formatting, security scanning
- **Docker**: Multi-architecture builds for AMD64 and ARM64
- **Releases**: Automated releases with Docker image publishing

### Workflow Triggers

- **Push**: `main`, `feature/*` branches
- **Pull Request**: `main` branch
- **Tags**: Version tags (`v*`) trigger releases

## Release Process

1. **Create and test your changes**:
   ```bash
   make test
   make lint
   make security
   ```

2. **Create a version tag**:
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

3. **Automated release**:
   - CI/CD runs all tests and builds
   - Docker images are built and pushed to ghcr.io
   - GitHub release is created with auto-generated notes
   - Release notes are automatically categorized (see below)

### Automatic Release Notes

The project uses GitHub's automatic release notes generation with custom categorization configured in `.github/release.yml`. PRs are automatically grouped into the following categories:

- **🚀 Features** - New features and enhancements
- **🐛 Bug Fixes** - Bug fixes and corrections  
- **🔒 Security** - Security-related changes
- **📦 Dependency Updates** - Renovate and dependency updates
- **🔧 Maintenance** - Refactoring and maintenance tasks
- **📚 Documentation** - Documentation improvements
- **⚡ Performance** - Performance optimizations
- **🧪 Testing** - Test-related changes
- **🔄 CI/CD** - CI/CD pipeline improvements

The configuration automatically groups Renovate dependency updates under "📦 Dependency Updates" based on the `dependencies` label assigned by Renovate. This keeps dependency updates separate from feature changes in release notes.

## Architecture

### Core Components

- **VideoMonitor**: Watches input directory using Linux inotify
- **VideoConverter**: Handles FFmpeg conversion with metadata embedding
- **HealthServer**: Provides monitoring endpoints for container orchestration
- **Config**: Environment-based configuration management

### Key Features

- **Asynchronous Processing**: Uses asyncio for concurrent operations
- **Retry Logic**: Exponential backoff for failed conversions
- **Metadata Preservation**: Embeds ID3/FLAC metadata from filenames and folder structure
- **Signal Handling**: Graceful shutdown with proper cleanup
- **Health Monitoring**: Built-in endpoints for container health checks

## Performance Considerations

- **Parallel Processing**: Configurable `MAX_PARALLEL_JOBS` (default: 4)
- **File Stability**: Waits for files to stabilize before processing
- **Memory Management**: Streaming file processing to handle large files
- **CPU Usage**: FFmpeg process management with proper cleanup

## Security

- **Non-root execution**: Container runs as UID 1000
- **Dependency scanning**: Automated security checks with Bandit and Safety
- **Input validation**: Safe filename handling and path traversal protection
- **Resource limits**: Configurable processing limits

## Troubleshooting

### Common Development Issues

1. **Tests failing**: Check FFmpeg installation and network connectivity
2. **Permission errors**: Ensure proper file permissions for input/output directories  
3. **Container issues**: Verify Docker daemon is running and accessible
4. **Linting errors**: Run `make lint-fix` to auto-fix formatting issues

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py

# Or with Docker
docker run -e LOG_LEVEL=DEBUG vidaud:latest
```

## Contributing Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Run tests** (`make test`)
4. **Check code quality** (`make lint`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Code Standards

- Follow PEP 8 (enforced by flake8)
- Use Black formatting (88 character line length)
- Add tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass

## Getting Help

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check the docs/ directory for detailed guides
