"""Integration tests with real video files."""

import asyncio
import os
import shutil
import tempfile
import time

import pytest
import requests

from src.config import Config
from src.converter import VideoConverter
from src.monitor import VideoMonitor


class TestRealVideoConversion:
    """Integration tests using real video samples."""

    def setup_method(self):
        """Setup test environment with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.input_dir)
        os.makedirs(self.output_dir)

        self.config = Config()
        self.config.input_dir = self.input_dir
        self.config.output_dir = self.output_dir
        self.config.stability_period = 1  # Short for testing

    def download_sample_file(self, url: str, filename: str) -> str:
        """Download a sample video file for testing."""
        file_path = os.path.join(self.input_dir, filename)

        # Skip download if file already exists (for faster repeated tests)
        if os.path.exists(file_path):
            return file_path

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(response.content)

            return file_path
        except Exception as e:
            pytest.skip(f"Could not download sample file: {e}")

    @pytest.mark.integration
    def test_ffmpeg_wmv_sample_mp3_conversion(self):
        """Test conversion of FFmpeg's official WMV sample to MP3."""
        # Download the official FFmpeg test sample
        sample_url = "https://samples.ffmpeg.org/testsuite/wmv1.wmv"
        sample_file = self.download_sample_file(sample_url, "wmv1.wmv")

        # Verify the file was downloaded
        assert os.path.exists(sample_file)
        assert os.path.getsize(sample_file) > 0

        # Configure for MP3 output
        self.config.output_format = "mp3"
        self.config.max_retries = 1  # Reduce retries for faster testing
        converter = VideoConverter(self.config)

        # Perform conversion synchronously for testing
        async def run_conversion():
            await converter.convert_file(sample_file)

        # Run conversion
        asyncio.run(run_conversion())

        # Verify output file exists
        expected_output = os.path.join(self.output_dir, "wmv1.mp3")
        assert os.path.exists(
            expected_output
        ), f"Output file not created: {expected_output}"

        # Verify output file has reasonable size (should be > 100KB for this sample)
        output_size = os.path.getsize(expected_output)
        assert output_size > 100000, f"Output file too small: {output_size} bytes"

        # Verify it's actually an MP3 file
        with open(expected_output, "rb") as f:
            header = f.read(3)
            # Check for ID3 tag or MP3 frame sync
            assert header == b"ID3" or header[:2] == b"\xff\xfb", "Not a valid MP3 file"

    @pytest.mark.integration
    def test_ffmpeg_wmv_sample_flac_conversion(self):
        """Test conversion of FFmpeg's official WMV sample to FLAC."""
        # Download the official FFmpeg test sample
        sample_url = "https://samples.ffmpeg.org/testsuite/wmv1.wmv"
        sample_file = self.download_sample_file(sample_url, "wmv1.wmv")

        # Configure for FLAC output with prefix
        self.config.output_format = "flac"
        self.config.filename_prefix = "test_"
        self.config.max_retries = 1  # Reduce retries for faster testing
        converter = VideoConverter(self.config)

        # Perform conversion
        async def run_conversion():
            await converter.convert_file(sample_file)

        asyncio.run(run_conversion())

        # Verify output file exists with prefix
        expected_output = os.path.join(self.output_dir, "test_wmv1.flac")
        assert os.path.exists(
            expected_output
        ), f"Output file not created: {expected_output}"

        # Verify output file has reasonable size (FLAC should be larger than MP3)
        output_size = os.path.getsize(expected_output)
        assert output_size > 400000, f"FLAC output file too small: {output_size} bytes"

        # Verify it's actually a FLAC file
        with open(expected_output, "rb") as f:
            header = f.read(4)
            assert header == b"fLaC", "Not a valid FLAC file"

    @pytest.mark.integration
    def test_metadata_extraction_from_filename(self):
        """Test metadata extraction from video filename."""
        # Download sample file
        sample_url = "https://samples.ffmpeg.org/testsuite/wmv1.wmv"
        sample_file = self.download_sample_file(sample_url, "Artist - Song Title.wmv")

        converter = VideoConverter(self.config)
        metadata = converter.extract_metadata_from_filename(sample_file)

        # Verify metadata extraction
        assert metadata["artist"] == "Artist"
        assert metadata["title"] == "Song Title"
        assert metadata["album"] == "input"  # Should be parent directory name
        assert metadata["track"] == "1"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_and_conversion(self):
        """Test complete end-to-end monitoring and conversion process."""
        # Configure monitor with shorter retry intervals to speed up cleanup
        self.config.max_retries = 1  # Limit retries
        self.config.retry_delay = 5  # Short retry delay

        monitor = VideoMonitor(self.config)

        # Start monitoring in background
        monitor_task = asyncio.create_task(monitor.start())

        try:
            # Wait a moment for monitoring to start
            await asyncio.sleep(0.5)

            # Download file while monitoring is active
            sample_url = "https://samples.ffmpeg.org/testsuite/wmv1.wmv"
            self.download_sample_file(sample_url, "wmv1.wmv")

            # Give monitor time to detect and process
            await asyncio.sleep(self.config.stability_period + 2)

            # Check if conversion occurred
            expected_output = os.path.join(self.output_dir, "wmv1.mp3")

            # Allow some extra time for processing
            max_wait = 15  # seconds
            start_time = time.time()

            while (
                not os.path.exists(expected_output)
                and (time.time() - start_time) < max_wait
            ):
                await asyncio.sleep(1)

            # Verify the file was converted
            assert os.path.exists(expected_output), "File was not converted by monitor"
            assert os.path.getsize(expected_output) > 100000, "Converted file too small"

            # Cancel converter IMMEDIATELY after verification to prevent new tasks
            monitor.converter.cancel()
            monitor._running = False

        finally:
            # Robust cleanup - ensure everything is cancelled
            monitor.converter.cancel()

            # Stop monitoring
            monitor._running = False

            # Cancel the monitor task
            monitor_task.cancel()

            # Wait for task cancellation with timeout
            try:
                await asyncio.wait_for(monitor_task, timeout=3.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

            # Ensure executor is shut down
            if hasattr(monitor, "executor"):
                monitor.executor.shutdown(wait=False)  # Don't wait to avoid hanging

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
