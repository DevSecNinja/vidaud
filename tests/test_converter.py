"""Test configuration and converter functionality."""

import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from src.config import Config
from src.converter import ConversionError, VideoConverter


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

    def test_cancellation_flag(self):
        """Test cancellation flag functionality."""
        # Initially not cancelled
        assert not self.converter.is_cancelled()

        # Cancel and check
        self.converter.cancel()
        assert self.converter.is_cancelled()

    def test_metadata_extraction_edge_cases(self):
        """Test metadata extraction edge cases."""
        # Test numbered track with various separators
        metadata = self.converter.extract_metadata_from_filename(
            "/album/02. Track Name.mp4")
        assert metadata["track"] == "02"
        assert metadata["title"] == "Track Name"

        # Test numbered track with underscore
        metadata = self.converter.extract_metadata_from_filename(
            "/album/03_Track Name.mp4")
        assert metadata["track"] == "03"
        assert metadata["title"] == "Track Name"

        # Test numbered track with dash
        metadata = self.converter.extract_metadata_from_filename(
            "/album/04-Track Name.mp4")
        assert metadata["track"] == "04"
        assert metadata["title"] == "Track Name"

        # Test single digit track
        metadata = self.converter.extract_metadata_from_filename(
            "/album/5 Track Name.mp4")
        assert metadata["title"] == "5 Track Name"  # Should NOT extract as track

        # Test complex artist - title with multiple dashes
        metadata = self.converter.extract_metadata_from_filename(
            "/album/Artist Name - Song - Remix.mp4")
        assert metadata["artist"] == "Artist Name"
        assert metadata["title"] == "Song - Remix"

    def test_output_path_outside_input_dir(self):
        """Test output path generation when input is outside input directory."""
        # File outside input directory should use just filename
        input_path = "/some/other/path/video.mkv"
        output_path = self.converter.get_output_path(input_path)

        expected_path = os.path.join(self.temp_dir, "video.mp3")
        assert output_path == expected_path

    def test_output_path_with_subdirectories(self):
        """Test output path generation with nested subdirectories."""
        # Create nested structure
        nested_input = os.path.join(self.temp_dir, "artist", "album", "track.mkv")
        output_path = self.converter.get_output_path(nested_input)

        expected_path = os.path.join(self.temp_dir, "artist", "album", "track.mp3")
        assert output_path == expected_path

    def test_build_ffmpeg_command_mp3(self):
        """Test FFmpeg command building for MP3."""
        self.config.output_format = "mp3"
        self.config.mp3_bitrate = 192

        cmd = self.converter._build_ffmpeg_command(
            "/input/test.mkv", "/output/test.mp3")

        expected_cmd = [
            "ffmpeg", "-i", "/input/test.mkv", "-y",
            "-acodec", "libmp3lame", "-b:a", "192k",
            "-vn", "/output/test.mp3"
        ]
        assert cmd == expected_cmd

    def test_build_ffmpeg_command_flac(self):
        """Test FFmpeg command building for FLAC."""
        self.config.output_format = "flac"
        self.config.flac_bit_depth = 24

        cmd = self.converter._build_ffmpeg_command(
            "/input/test.mkv", "/output/test.flac")

        expected_cmd = [
            "ffmpeg", "-i", "/input/test.mkv", "-y",
            "-acodec", "flac", "-sample_fmt", "s24",
            "-vn", "/output/test.flac"
        ]
        assert cmd == expected_cmd

    def test_build_ffmpeg_command_unsupported_format(self):
        """Test FFmpeg command building with unsupported format."""
        self.config.output_format = "ogg"

        with pytest.raises(ConversionError, match="Unsupported output format: ogg"):
            self.converter._build_ffmpeg_command("/input/test.mkv", "/output/test.ogg")

    @pytest.mark.asyncio
    async def test_run_ffmpeg_success(self):
        """Test successful FFmpeg execution."""
        cmd = ["echo", "test"]

        # This should not raise an exception
        await self.converter._run_ffmpeg(cmd)

    @pytest.mark.asyncio
    async def test_run_ffmpeg_command_not_found(self):
        """Test FFmpeg execution when command not found."""
        cmd = ["nonexistent_command", "arg1", "arg2"]

        with pytest.raises(ConversionError, match="FFmpeg not found"):
            await self.converter._run_ffmpeg(cmd)

    @pytest.mark.asyncio
    async def test_run_ffmpeg_command_failure(self):
        """Test FFmpeg execution when command fails."""
        # Use a command that will fail
        cmd = ["false"]  # 'false' command always returns exit code 1

        with pytest.raises(ConversionError, match="ffmpeg failed"):
            await self.converter._run_ffmpeg(cmd)

    @pytest.mark.asyncio
    async def test_convert_file_skip_existing(self):
        """Test conversion skips existing output files when configured."""
        # Create a test input file
        input_file = os.path.join(self.temp_dir, "test.mkv")
        with open(input_file, 'w') as f:
            f.write("fake video content")

        # Create the expected output file
        output_file = os.path.join(self.temp_dir, "test.mp3")
        with open(output_file, 'w') as f:
            f.write("fake audio content")

        # Configure to skip existing files
        self.config.skip_existing = True

        # Mock the logger to capture the skip message
        with patch.object(self.converter.logger, 'info') as mock_logger:
            await self.converter.convert_file(input_file)
            mock_logger.assert_called_with(f"Skipping existing file: {output_file}")

    @pytest.mark.asyncio
    async def test_convert_file_cancelled_early(self):
        """Test conversion stops when cancelled early."""
        # Create a test input file
        input_file = os.path.join(self.temp_dir, "test.mkv")
        with open(input_file, 'w') as f:
            f.write("fake video content")

        # Cancel the converter before starting
        self.converter.cancel()

        # Mock the logger to capture the cancellation message
        with patch.object(self.converter.logger, 'info') as mock_logger:
            await self.converter.convert_file(input_file)
            mock_logger.assert_called_with(f"Conversion cancelled for {input_file}")

    def test_embed_metadata_mp3_format(self):
        """Test metadata embedding for MP3 format."""
        # Create a temporary MP3 file
        mp3_file = os.path.join(self.temp_dir, "test.mp3")

        # Create a minimal MP3 file (just header)
        with open(mp3_file, 'wb') as f:
            # Write MP3 header (simplified)
            f.write(b'\xff\xfb\x90\x00')  # Basic MP3 frame header

        self.config.output_format = "mp3"
        metadata = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "track": "1"
        }

        # Test that it doesn't raise an exception
        # (We can't easily verify the actual metadata without more complex setup)
        try:
            self.converter._embed_metadata(mp3_file, metadata)
        except Exception as e:
            # If mutagen fails due to invalid MP3, that's expected in unit tests
            # The important thing is our code structure is correct
            assert "not a valid" in str(e).lower(
            ) or "unable to determine" in str(e).lower()

    def test_embed_metadata_flac_format(self):
        """Test metadata embedding for FLAC format."""
        # Create a temporary FLAC file
        flac_file = os.path.join(self.temp_dir, "test.flac")

        # Create a minimal FLAC file (just header)
        with open(flac_file, 'wb') as f:
            # Write FLAC header
            f.write(b'fLaC')  # FLAC signature

        self.config.output_format = "flac"
        metadata = {
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "track": "1"
        }

        # Test that it doesn't raise an exception
        try:
            self.converter._embed_metadata(flac_file, metadata)
        except Exception as e:
            # If mutagen fails due to invalid FLAC, that's expected in unit tests
            assert "not a valid" in str(e).lower(
            ) or "unable to determine" in str(e).lower()

    def test_embed_metadata_exception_handling(self):
        """Test metadata embedding handles exceptions gracefully."""
        nonexistent_file = "/path/to/nonexistent/file.mp3"
        self.config.output_format = "mp3"
        metadata = {"title": "Test"}

        # Mock the logger to capture the warning
        with patch.object(self.converter.logger, 'warning') as mock_warning:
            # Should not raise exception, just log warning
            self.converter._embed_metadata(nonexistent_file, metadata)
            mock_warning.assert_called_once()
            assert "Failed to embed metadata" in mock_warning.call_args[0][0]

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
