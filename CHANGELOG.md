# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-08-12

Initial MVP release

### Added

- Initial release of vidaud video-to-audio converter
- Automatic video file monitoring with inotify
- Support for MKV, WebM, MP4, AVI, MOV, WMV input formats
- MP3 and FLAC output format support
- Metadata embedding (Title, Artist, Album, Track)
- Configurable filename prefix/postfix
- Parallel processing with configurable job count
- File stability detection to avoid processing partial files
- Retry logic for failed conversions
- Health check and metrics endpoints
- Docker support with multi-architecture builds (ARM64, x86_64)
- Non-root container execution for security
- Comprehensive test suite
- GitHub Actions CI/CD pipeline
- Renovate dependency management
- Integration tests using official FFmpeg test samples from https://samples.ffmpeg.org/
- Comprehensive Docker Compose testing and validation
- FFmpeg acknowledgments in README
- Test markers for unit vs integration tests (`pytest -m integration`)
- New Makefile targets: `test-unit`, `test-integration`

### Security

- Runs as non-root user (UID 1000)
- Security scanning in CI pipeline
- Regular dependency updates via Renovate
