"""Configuration management for vidaud."""

import os


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        # Input/Output directories (F4)
        self.input_dir: str = os.getenv("INPUT_DIR", "/input")
        self.output_dir: str = os.getenv("OUTPUT_DIR", "/output")

        # Output format configuration (F2, F3)
        self.output_format: str = os.getenv("OUTPUT_FORMAT", "mp3").lower()
        if self.output_format not in ["mp3", "flac"]:
            raise ValueError(f"Unsupported output format: {self.output_format}")

        # File naming configuration (F7)
        self.filename_prefix: str = os.getenv("FILENAME_PREFIX", "")
        self.filename_postfix: str = os.getenv("FILENAME_POSTFIX", "")

        # Parallel processing configuration (F8)
        self.max_parallel_jobs: int = int(os.getenv("MAX_PARALLEL_JOBS", "4"))

        # File stability configuration (F10)
        self.stability_period: int = int(os.getenv("STABILITY_PERIOD_SECONDS", "30"))

        # Retry configuration (F12)
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay: int = int(os.getenv("RETRY_DELAY_SECONDS", "60"))

        # File handling configuration (F15)
        self.skip_existing: bool = os.getenv("SKIP_EXISTING", "true").lower() == "true"

        # Audio encoding configuration
        self.mp3_bitrate: int = int(os.getenv("MP3_BITRATE", "320"))
        self.flac_bit_depth: int = int(os.getenv("FLAC_BIT_DEPTH", "16"))

        # Logging configuration (F16)
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        if self.log_level not in ["DEBUG", "INFO", "WARN", "ERROR"]:
            self.log_level = "INFO"

        # Health server configuration (NF12)
        self.health_port: int = int(os.getenv("HEALTH_PORT", "8080"))

        # File monitoring configuration (F14)
        self.polling_interval: int = int(os.getenv("POLLING_INTERVAL_SECONDS", "10"))

        # Supported video formats (F2)
        self.supported_formats: set = {".mkv", ".webm", ".mp4", ".avi", ".mov", ".wmv"}

    def get_output_filename(self, input_path: str) -> str:
        """Generate output filename with prefix/postfix."""
        input_file = os.path.basename(input_path)
        name_without_ext = os.path.splitext(input_file)[0]

        # Apply prefix and postfix (F7)
        output_name = f"{self.filename_prefix}{name_without_ext}{self.filename_postfix}"

        # Add appropriate extension
        extension = ".flac" if self.output_format == "flac" else ".mp3"
        return f"{output_name}{extension}"
