"""Test configuration and converter functionality."""

import os
import shutil
import tempfile

import pytest

from src.config import Config
from src.converter import VideoConverter


class TestConfig:
    """Test configuration management."""

    def test_default_values(self):
        """Test default configuration values."""
        # Set up clean environment
        env_vars_to_clear = [
            "INPUT_DIR",
            "OUTPUT_DIR",
            "OUTPUT_FORMAT",
            "FILENAME_PREFIX",
            "FILENAME_POSTFIX",
            "MAX_PARALLEL_JOBS",
            "STABILITY_PERIOD_SECONDS",
            "MAX_RETRIES",
            "RETRY_DELAY_SECONDS",
            "LOG_LEVEL",
            "HEALTH_PORT",
            "POLLING_INTERVAL_SECONDS",
        ]

        original_values = {}
        for var in env_vars_to_clear:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            config = Config()
            assert config.input_dir == "/input"
            assert config.output_dir == "/output"
            assert config.output_format == "mp3"
            assert config.max_parallel_jobs == 4
            assert config.log_level == "INFO"
        finally:
            # Restore environment
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_environment_override(self):
        """Test environment variable overrides."""
        os.environ["OUTPUT_FORMAT"] = "flac"
        os.environ["MAX_PARALLEL_JOBS"] = "8"
        os.environ["LOG_LEVEL"] = "DEBUG"

        try:
            config = Config()
            assert config.output_format == "flac"
            assert config.max_parallel_jobs == 8
            assert config.log_level == "DEBUG"
        finally:
            del os.environ["OUTPUT_FORMAT"]
            del os.environ["MAX_PARALLEL_JOBS"]
            del os.environ["LOG_LEVEL"]

    def test_invalid_output_format(self):
        """Test invalid output format raises error."""
        os.environ["OUTPUT_FORMAT"] = "invalid"

        try:
            with pytest.raises(ValueError):
                Config()
        finally:
            del os.environ["OUTPUT_FORMAT"]

    def test_filename_generation(self):
        """Test filename generation with prefix/postfix."""
        os.environ["FILENAME_PREFIX"] = "audio_"
        os.environ["FILENAME_POSTFIX"] = "_converted"
        os.environ["OUTPUT_FORMAT"] = "mp3"

        try:
            config = Config()
            output_name = config.get_output_filename("/path/to/video.mkv")
            assert output_name == "audio_video_converted.mp3"
        finally:
            del os.environ["FILENAME_PREFIX"]
            del os.environ["FILENAME_POSTFIX"]
            del os.environ["OUTPUT_FORMAT"]


class TestVideoConverter:
    """Test video conversion functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.input_dir = self.temp_dir
        self.config.output_dir = self.temp_dir
        self.converter = VideoConverter(self.config)

    def test_metadata_extraction(self):
        """Test metadata extraction from filenames (F6)."""
        # Test basic filename
        metadata = self.converter.extract_metadata_from_filename("/path/album/song.mp4")
        assert metadata["title"] == "song"
        assert metadata["album"] == "album"

        # Test artist - title format
        metadata = self.converter.extract_metadata_from_filename(
            "/path/album/Artist - Song Title.mp4"
        )
        assert metadata["artist"] == "Artist"
        assert metadata["title"] == "Song Title"

        # Test track number format
        metadata = self.converter.extract_metadata_from_filename(
            "/path/album/01 - Song Title.mp4"
        )
        assert metadata["track"] == "01"
        assert metadata["title"] == "Song Title"

    def test_output_path_generation(self):
        """Test output path generation maintains structure (F4)."""
        input_path = os.path.join(self.temp_dir, "subdir", "video.mkv")
        output_path = self.converter.get_output_path(input_path)

        expected_path = os.path.join(self.temp_dir, "subdir", "video.mp3")
        assert output_path == expected_path

    def test_temp_file_naming(self):
        """Test temporary file naming (F11)."""
        final_path = "/output/test.mp3"
        temp_path = self.converter.get_temp_output_path(final_path)

        assert temp_path.startswith("/output/.tmp_test_")
        assert temp_path.endswith(".mp3")
        assert temp_path != final_path

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
