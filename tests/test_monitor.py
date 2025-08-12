"""Test file monitoring functionality."""

import asyncio
import os
import shutil
import tempfile
import time

import pytest

from src.config import Config
from src.monitor import FileTracker, VideoMonitor


class TestFileTracker:
    """Test file tracking for duplicate prevention (NF3)."""

    def setup_method(self):
        """Setup test environment."""
        self.tracker = FileTracker()
        self.temp_dir = tempfile.mkdtemp()

    def test_processing_state_management(self):
        """Test processing state management."""
        file_path = "/test/video.mp4"

        # Initially not processed or processing
        assert not self.tracker.is_processed(file_path)
        assert not self.tracker.is_processing(file_path)

        # Start processing
        assert self.tracker.start_processing(file_path)
        assert self.tracker.is_processing(file_path)
        assert not self.tracker.start_processing(file_path)  # Can't start again

        # Finish processing
        self.tracker.finish_processing(file_path, success=True)
        assert not self.tracker.is_processing(file_path)
        assert self.tracker.is_processed(file_path)

    def test_duplicate_detection_by_path(self):
        """Test duplicate detection by file path."""
        file_path = "/test/video.mp4"

        self.tracker.finish_processing(file_path, success=True)
        assert self.tracker.is_processed(file_path)

        # Same path should be detected as processed
        assert self.tracker.is_processed(file_path)

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestVideoMonitor:
    """Test video monitoring functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.input_dir = self.temp_dir
        self.config.output_dir = self.temp_dir
        self.config.stability_period = 1  # Short period for testing
        self.monitor = VideoMonitor(self.config)

    def test_video_file_detection(self):
        """Test video file format detection."""
        assert self.monitor.is_video_file("/path/video.mp4")
        assert self.monitor.is_video_file("/path/video.mkv")
        assert self.monitor.is_video_file("/path/video.webm")
        assert not self.monitor.is_video_file("/path/audio.mp3")
        assert not self.monitor.is_video_file("/path/document.txt")

    def test_file_stability_check(self):
        """Test file stability detection (F10)."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.mp4")
        with open(test_file, "wb") as f:
            f.write(b"test content")

        # File should not be stable immediately
        assert not self.monitor.is_file_stable(test_file)

        # Wait for stability period
        time.sleep(self.config.stability_period + 0.1)
        assert self.monitor.is_file_stable(test_file)

        # Empty file should not be stable
        empty_file = os.path.join(self.temp_dir, "empty.mp4")
        with open(empty_file, "wb") as f:
            pass  # Create empty file
        time.sleep(self.config.stability_period + 0.1)
        assert not self.monitor.is_file_stable(empty_file)

    def test_file_queuing(self):
        """Test file queuing for processing."""
        test_file = os.path.join(self.temp_dir, "test.mp4")

        # Queue non-existent file (should work)
        self.monitor.queue_file_for_processing(test_file)
        assert test_file in self.monitor.pending_files

        # Queue non-video file (should be ignored)
        text_file = os.path.join(self.temp_dir, "test.txt")
        self.monitor.queue_file_for_processing(text_file)
        assert text_file not in self.monitor.pending_files

    @pytest.mark.asyncio
    async def test_pending_file_processing(self):
        """Test processing of pending files."""
        # Create a test video file
        test_file = os.path.join(self.temp_dir, "test.mp4")
        with open(test_file, "wb") as f:
            f.write(b"test video content")

        # Queue the file
        self.monitor.queue_file_for_processing(test_file)
        assert test_file in self.monitor.pending_files

        # Wait for stability period
        await asyncio.sleep(self.config.stability_period + 0.1)

        # Process pending files (this will try to convert, but we expect it to fail gracefully)
        await self.monitor.process_pending_files()

        # File should be removed from pending (either processed or failed)
        assert test_file not in self.monitor.pending_files

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
