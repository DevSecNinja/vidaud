# vidaud - Video to Audio Converter

[![CI/CD Pipeline](https://github.com/DevSecNinja/vidaud/actions/workflows/ci.yml/badge.svg)](https://github.com/DevSecNinja/vidaud/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/DevSecNinja/vidaud/graph/badge.svg?token=YV0843JC3Z)](https://codecov.io/github/DevSecNinja/vidaud)

A Docker-based application that automatically converts video files to audio formats (MP3/FLAC) while preserving metadata and folder structure for Plex compatibility.

## ✨ Features

- **🔄 Automatic Monitoring**: Watches directories for new video files using efficient inotify
- **🎵 Format Support**: Converts MKV, WebM, MP4, AVI, MOV, WMV to MP3 or FLAC
- **📝 Metadata Preservation**: Embeds title, artist, album, and track information
- **📁 Folder Structure**: Maintains original directory structure in output
- **⚡ Parallel Processing**: Configurable concurrent conversion jobs
- **🛡️ File Safety**: Prevents processing of partial/incomplete files
- **🔄 Retry Logic**: Automatic retry with exponential backoff for failed conversions
- **❤️ Health Monitoring**: Built-in health check and metrics endpoints
- **🔒 Security**: Runs as non-root user in container
- **🌐 Multi-Architecture**: Supports both x86_64 and ARM64 platforms

## 🚀 Quick Start

### Using Docker

```bash
docker run -d \
  --name vidaud \
  -v /path/to/videos:/input:ro \
  -v /path/to/audio:/output \
  -p 8080:8080 \
  ghcr.io/devsecninja/vidaud:latest
```

### Using Docker Compose

1. **Download the compose file:**
   ```bash
   curl -O https://raw.githubusercontent.com/devsecninja/vidaud/main/docker-compose.yml
   ```

2. **Edit the volumes** in `docker-compose.yml`:
   ```yaml
   volumes:
     - /your/video/path:/input:ro     # Replace with your video directory
     - /your/audio/path:/output       # Replace with your audio directory
   ```

3. **Start the service:**
   ```bash
   docker-compose up -d
   ```

4. **Check the health:**
   ```bash
   curl http://localhost:8080/health
   ```

## ⚙️ Configuration

All configuration is done through environment variables. Here are the most commonly used options:

| Variable            | Default | Description                              |
| ------------------- | ------- | ---------------------------------------- |
| `OUTPUT_FORMAT`     | `mp3`   | Output format: `mp3` or `flac`           |
| `MP3_BITRATE`       | `320`   | MP3 bitrate in kbps (128, 192, 320)      |
| `FLAC_BIT_DEPTH`    | `16`    | FLAC bit depth (16, 24)                  |
| `MAX_PARALLEL_JOBS` | `4`     | Number of concurrent conversion jobs     |
| `SKIP_EXISTING`     | `true`  | Skip conversion if output file exists    |
| `LOG_LEVEL`         | `INFO`  | Logging level (DEBUG, INFO, WARN, ERROR) |

### Example Configurations

**High-Quality FLAC Output:**

```bash
docker run -d \
  --name vidaud-flac \
  -v /path/to/videos:/input:ro \
  -v /path/to/audio:/output \
  -e OUTPUT_FORMAT=flac \
  -e FLAC_BIT_DEPTH=24 \
  -e FILENAME_PREFIX="lossless_" \
  ghcr.io/devsecninja/vidaud:latest
```

**Performance Tuning:**

```bash
docker run -d \
  --name vidaud-performance \
  -v /path/to/videos:/input:ro \
  -v /path/to/audio:/output \
  -e MAX_PARALLEL_JOBS=8 \
  -e STABILITY_PERIOD_SECONDS=10 \
  --cpus="4.0" \
  --memory="4g" \
  ghcr.io/devsecninja/vidaud:latest
```

📋 **See [Configuration Reference](docs/CONFIGURATION.md) for all available options and detailed examples.**

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8080/health
```

### Metrics

```bash
curl http://localhost:8080/metrics
```

### Logs

```bash
# View container logs
docker logs vidaud

# Follow logs in real-time
docker logs -f vidaud
```

## 📁 File Naming & Metadata

The application intelligently extracts metadata from filenames and folder structures:

- **`Artist - Title.mp4`** → Artist and Title metadata
- **`01 - Song Title.mp4`** → Track number and Title metadata
- **`/Artist/Album/Song.mp4`** → Artist, Album, and Title metadata

## 🎯 Supported Formats

**Input:** MKV, WebM, MP4, AVI, MOV, WMV
**Output:** MP3 (320kbps, 44.1kHz) or FLAC (lossless)

## 🔧 Troubleshooting

### Common Issues

**Permission Errors:**

- Ensure the container user (UID 1000) has write access to output directory
- Use `sudo chown -R 1000:1000 /your/audio/path`

**No Files Processed:**

- Check that input files are in supported formats
- Verify files are stable (not being written to)
- Check logs: `docker logs vidaud`

**High CPU Usage:**

- Reduce `MAX_PARALLEL_JOBS` for lower-end systems
- Set Docker resource limits: `--cpus="2.0" --memory="2g"`

**Health Check Issues:**

- Ensure port 8080 is accessible
- Check container status: `docker ps`
- View detailed logs for error messages

### Debug Mode

```bash
docker run -d \
  --name vidaud-debug \
  -v /path/to/videos:/input:ro \
  -v /path/to/audio:/output \
  -e LOG_LEVEL=DEBUG \
  ghcr.io/devsecninja/vidaud:latest
```

## 📚 Documentation

- **[Configuration Reference](docs/CONFIGURATION.md)** - Complete configuration options and examples
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development setup and guidelines
- **[Code Quality](docs/code-quality.md)** - Development tools and standards

## 🤝 Contributing

Contributions are welcome! Please see the [Contributing Guide](docs/CONTRIBUTING.md) for development setup and guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[FFmpeg Team](https://ffmpeg.org/)** - This project relies on the excellent FFmpeg library
- **[FFmpeg Test Samples](https://samples.ffmpeg.org/)** - Integration tests use official test samples

---

⭐ **Star this repository if you find it useful!**
