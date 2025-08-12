# vidau Requirements

## `vidaud` Requirements Table

| Ref | Requirement | MoSCoW Priority | Notes |
|-----|-------------|-----------------|-------|
| F1  | Watch mounted volume and nested directories for new video files | **Must** | Use efficient monitoring like `inotify` |
| F2  | Convert `mkv`, `webm` and `mp4` video files to `mp3` by default | **Must** | Plex-compatible lossy output |
| F3  | Support lossless FLAC output | **Must** | Configurable via environment variable |
| F4  | Maintain original folder structure for output | **Must** | Plex indexing consistency |
| F5  | Plex-compatible naming for audio files | **Must** | Artist - Track format |
| F6  | Embed audio metadata (Title, Artist, Album, Track #) | **Must** | Plex music recognition |
| F7  | Configurable filename prefix/postfix | **Must** | Environment variable support |
| F8  | Support parallel processing with configurable job count | **Must** | Prevents bottlenecks |
| F9  | Thread/process safety for parallel jobs | **Must** | Avoids duplicate or conflicting processing |
| F10 | Detect and avoid partial files until stable | **Must** | Configurable stability period |
| F11 | Use temporary file naming until conversion finishes | **Must** | Prevent Plex indexing incomplete files |
| F12 | Retry failed conversions (configurable attempts) | **Must** | Logs permanent failures after retries |
| F13 | Support long file paths without errors | **Must** | Especially for NAS setups |
| F14 | Allow HDDs to spin down when idle | **Must** | Avoid aggressive polling |
| F15 | Log major events to stdout/stderr | **Must** | For Docker logging driver |
| F16 | Log levels: DEBUG, INFO, WARN, ERROR | **Must** | Configurable verbosity |
| F17 | Automated tests for file conversion, prefix/postfix, metadata, retries | **Must** | Must run locally & in CI |
| F18 | Build & release automation via GitHub Actions | **Must** | Easy to make changes |
| F19 | Semantic Versioning for releases | **Must** | e.g., 1.0.0 |
| F20 | Dependency updates managed by Renovate | **Must** | Automated PRs for updates |
| F21 | Local Docker build without dependencies from e.g. pipeline artifacts | **Must** | Developer-friendly |
| F22 | Docker image must be published as a GitHub Artifact | **Must** | Easy to deploy |
| NF1 | Lightweight container with minimal dependencies | **Must** | Fast startup & low footprint |
| NF2 | Graceful handling of corrupted video files | **Must** | No crash on failure |
| NF3 | Avoid duplicate processing of same file | **Must** | Use file hashing or locking |
| NF4 | Multi-arch Docker images (ARM & x86_64) | **Should** | Expands compatibility for NAS/RPi |
| NF5 | Run as non-root | **Must** | Improves security posture |
| NF6 | Keep dependencies up to date & free from known vulnerabilities | **Must** | Security requirement |
| NF7 | Clean, modular, documented codebase | **Must** | Maintainability |
| NF8 | Detailed logs with timestamps and file paths | **Must** | For debugging |
| NF9 | Configurable output formats beyond MP3/FLAC | **Could** | AAC, WAV in future |
| NF10 | Batch processing for large initial imports | **Could** | Speeds up onboarding |
| NF11 | Webhook integration to trigger Plex library refresh | **Could** | Improves automation |
| NF12 | Resource usage metrics & health endpoint | **Could** | For monitoring |
