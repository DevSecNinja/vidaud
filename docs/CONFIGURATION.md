# Configuration Reference

Complete reference for all configuration options available in vidaud.

## Environment Variables

All configuration is done through environment variables. Below is a comprehensive table of all available options:

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| **INPUT_DIR** | Path | `/input` | Directory to monitor for video files | `/mnt/videos` |
| **OUTPUT_DIR** | Path | `/output` | Directory for converted audio files | `/mnt/audio` |
| **OUTPUT_FORMAT** | String | `mp3` | Output audio format | `mp3`, `flac` |
| **FILENAME_PREFIX** | String | `` | Prefix added to all output filenames | `converted_` |
| **FILENAME_POSTFIX** | String | `` | Postfix added to all output filenames | `_processed` |
| **MP3_BITRATE** | Integer | `320` | MP3 bitrate in kbps | `128`, `192`, `320` |
| **FLAC_BIT_DEPTH** | Integer | `16` | FLAC bit depth | `16`, `24` |
| **SKIP_EXISTING** | Boolean | `true` | Skip conversion if output file exists | `true`, `false` |
| **MAX_PARALLEL_JOBS** | Integer | `4` | Number of concurrent conversion jobs | `1`, `8`, `16` |
| **STABILITY_PERIOD_SECONDS** | Integer | `30` | Wait time before processing new files | `10`, `60`, `120` |
| **MAX_RETRIES** | Integer | `3` | Number of retry attempts for failed conversions | `1`, `5`, `10` |
| **RETRY_DELAY_SECONDS** | Integer | `60` | Base delay between retry attempts | `30`, `120`, `300` |
| **POLLING_INTERVAL_SECONDS** | Integer | `10` | Interval for checking pending files | `5`, `15`, `30` |
| **LOG_LEVEL** | String | `INFO` | Logging verbosity level | `DEBUG`, `INFO`, `WARN`, `ERROR` |
| **HEALTH_PORT** | Integer | `8080` | Port for health check endpoint | `8080`, `9000` |

## Docker Run Examples

### Basic Usage
```bash
docker run -d \
  --name vidaud \
  -v /host/videos:/input:ro \
  -v /host/audio:/output \
  ghcr.io/devsecninja/vidaud:latest
```

### High-Quality FLAC Output
```bash
docker run -d \
  --name vidaud-flac \
  -v /host/videos:/input:ro \
  -v /host/audio:/output \
  -e OUTPUT_FORMAT=flac \
  -e FLAC_BIT_DEPTH=24 \
  -e FILENAME_PREFIX="hq_" \
  ghcr.io/devsecninja/vidaud:latest
```

### Performance Tuning
```bash
docker run -d \
  --name vidaud-performance \
  -v /host/videos:/input:ro \
  -v /host/audio:/output \
  -e MAX_PARALLEL_JOBS=8 \
  -e STABILITY_PERIOD_SECONDS=10 \
  -e POLLING_INTERVAL_SECONDS=5 \
  --cpus="4.0" \
  --memory="4g" \
  ghcr.io/devsecninja/vidaud:latest
```

### Debug Configuration
```bash
docker run -d \
  --name vidaud-debug \
  -v /host/videos:/input:ro \
  -v /host/audio:/output \
  -e LOG_LEVEL=DEBUG \
  -e MAX_RETRIES=1 \
  -e RETRY_DELAY_SECONDS=30 \
  ghcr.io/devsecninja/vidaud:latest
```

## Docker Compose Configuration

### Basic Setup
```yaml
services:
  vidaud:
    image: ghcr.io/devsecninja/vidaud:latest
    container_name: vidaud
    volumes:
      - /host/videos:/input:ro
      - /host/audio:/output
    environment:
      - OUTPUT_FORMAT=mp3
      - MP3_BITRATE=320
    ports:
      - "8080:8080"
    restart: unless-stopped
```

### Advanced Configuration
```yaml
services:
  vidaud:
    image: ghcr.io/devsecninja/vidaud:latest
    container_name: vidaud
    volumes:
      - /mnt/media/videos:/input:ro
      - /mnt/media/audio:/output
      - /var/log/vidaud:/logs
    environment:
      # Output Configuration
      - OUTPUT_FORMAT=flac
      - FLAC_BIT_DEPTH=24
      - FILENAME_PREFIX=converted_
      - SKIP_EXISTING=true
      
      # Performance Settings
      - MAX_PARALLEL_JOBS=6
      - STABILITY_PERIOD_SECONDS=15
      - POLLING_INTERVAL_SECONDS=5
      
      # Retry Configuration
      - MAX_RETRIES=5
      - RETRY_DELAY_SECONDS=120
      
      # Logging
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
```

## Configuration Details

### File Format Support

**Input Formats:**
- MKV (Matroska Video)
- WebM (Web Media)
- MP4 (MPEG-4)
- AVI (Audio Video Interleave)
- MOV (QuickTime Movie)
- WMV (Windows Media Video)

**Output Formats:**
- **MP3**: Lossy compression, Plex-compatible
  - Bitrates: 128, 192, 256, 320 kbps
  - Sample rate: 44.1 kHz
  - Channels: Stereo
- **FLAC**: Lossless compression
  - Bit depths: 16, 24 bits
  - Sample rates: Preserved from source
  - Channels: Preserved from source

### Performance Guidelines

**CPU-bound workloads:**
- Set `MAX_PARALLEL_JOBS` to match CPU cores
- Higher values may cause system overload

**I/O-bound workloads:**
- Increase `MAX_PARALLEL_JOBS` beyond CPU cores
- Consider storage speed and network latency

**Memory considerations:**
- Each job uses ~100-500MB depending on file size
- Monitor memory usage with multiple jobs

**Storage optimization:**
- Use `SKIP_EXISTING=true` to avoid reprocessing
- Consider separate volumes for input and output

### Retry Logic

The application implements exponential backoff for failed conversions:

1. **First attempt**: Immediate processing
2. **First retry**: Wait `RETRY_DELAY_SECONDS`
3. **Second retry**: Wait `RETRY_DELAY_SECONDS * 2`
4. **Third retry**: Wait `RETRY_DELAY_SECONDS * 4`
5. **Continue** until `MAX_RETRIES` reached

### Health Monitoring

**Health endpoint**: `http://localhost:8080/health`
```json
{
  "status": "healthy",
  "timestamp": "2025-08-12T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

**Metrics endpoint**: `http://localhost:8080/metrics`
```json
{
  "files_processed": 42,
  "files_failed": 1,
  "active_jobs": 2,
  "pending_files": 0,
  "total_processing_time": 1800.5
}
```

### Security Considerations

- **User permissions**: Container runs as UID 1000 (non-root)
- **File access**: Use read-only mounts for input directories
- **Network exposure**: Only expose health port if needed
- **Resource limits**: Set appropriate CPU and memory limits

### Troubleshooting Configuration

**High CPU usage:**
```bash
# Reduce parallel jobs
-e MAX_PARALLEL_JOBS=2
```

**Slow processing:**
```bash
# Increase parallel jobs (if system can handle it)
-e MAX_PARALLEL_JOBS=8
# Reduce stability wait time
-e STABILITY_PERIOD_SECONDS=10
```

**Memory issues:**
```bash
# Reduce parallel jobs
-e MAX_PARALLEL_JOBS=1
# Add Docker memory limit
--memory="2g"
```

**File detection issues:**
```bash
# Increase polling frequency
-e POLLING_INTERVAL_SECONDS=5
# Increase stability period
-e STABILITY_PERIOD_SECONDS=60
```

**Network errors (for integration tests):**
```bash
# Increase retry settings
-e MAX_RETRIES=10
-e RETRY_DELAY_SECONDS=300
```
