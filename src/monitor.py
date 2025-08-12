"""Video file monitoring using inotify for efficient directory watching."""

import asyncio
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import Dict, Set, Optional
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import Config
from .converter import VideoConverter


class FileTracker:
    """Tracks file processing state to avoid duplicates (NF3)."""

    def __init__(self):
        self._processed_files: Set[str] = set()
        self._processing_files: Set[str] = set()
        self._file_hashes: Dict[str, str] = {}
        self._lock = Lock()

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate file hash to detect duplicates."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to hash {file_path}: {e}")
            return None

    def is_processed(self, file_path: str) -> bool:
        """Check if file has already been processed."""
        with self._lock:
            # Check by path first
            if file_path in self._processed_files:
                return True

            # Check by hash for moved/renamed files
            file_hash = self.get_file_hash(file_path)
            if file_hash and file_hash in self._file_hashes.values():
                return True

            return False

    def is_processing(self, file_path: str) -> bool:
        """Check if file is currently being processed."""
        with self._lock:
            return file_path in self._processing_files

    def start_processing(self, file_path: str) -> bool:
        """Mark file as being processed. Returns False if already processing."""
        with self._lock:
            if file_path in self._processing_files:
                return False
            self._processing_files.add(file_path)
            return True

    def finish_processing(self, file_path: str, success: bool = True):
        """Mark file processing as complete."""
        with self._lock:
            self._processing_files.discard(file_path)
            if success:
                self._processed_files.add(file_path)
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    self._file_hashes[file_path] = file_hash


class VideoFileHandler(FileSystemEventHandler):
    """Handles video file events from directory monitoring."""

    def __init__(self, monitor: "VideoMonitor"):
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.logger.debug(f"File created: {event.src_path}")
            self.monitor.queue_file_for_processing(event.src_path)

    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory:
            self.logger.debug(f"File moved: {event.dest_path}")
            self.monitor.queue_file_for_processing(event.dest_path)

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            # Only queue if file is stable (not being written to)
            self.logger.debug(f"File modified: {event.src_path}")
            self.monitor.queue_file_for_processing(event.src_path)


class VideoMonitor:
    """Main video file monitoring and processing coordinator."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.converter = VideoConverter(config)
        self.file_tracker = FileTracker()
        self.observer = Observer()
        self.executor = ThreadPoolExecutor(max_workers=config.max_parallel_jobs)
        self.pending_files: Dict[str, float] = {}  # file_path -> timestamp
        self._running = False

    def is_video_file(self, file_path: str) -> bool:
        """Check if file is a supported video format."""
        return Path(file_path).suffix.lower() in self.config.supported_formats

    def is_file_stable(self, file_path: str) -> bool:
        """Check if file is stable (not being written to) (F10)."""
        try:
            stat = os.stat(file_path)
            current_time = time.time()

            # Check if file was modified recently
            if current_time - stat.st_mtime < self.config.stability_period:
                return False

            # Check if file size is reasonable (not 0 bytes)
            if stat.st_size == 0:
                return False

            return True
        except (OSError, FileNotFoundError):
            return False

    def queue_file_for_processing(self, file_path: str):
        """Queue a file for processing after stability check."""
        if not self.is_video_file(file_path):
            return

        if self.file_tracker.is_processed(file_path):
            self.logger.debug(f"File already processed: {file_path}")
            return

        if self.file_tracker.is_processing(file_path):
            self.logger.debug(f"File already being processed: {file_path}")
            return

        # Add to pending files with current timestamp
        self.pending_files[file_path] = time.time()
        self.logger.info(f"Queued file for processing: {file_path}")

    async def process_pending_files(self):
        """Process files that are stable and ready for conversion."""
        current_time = time.time()
        ready_files = []

        # Find files that are ready for processing
        for file_path, queue_time in list(self.pending_files.items()):
            if current_time - queue_time >= self.config.stability_period:
                if os.path.exists(file_path) and self.is_file_stable(file_path):
                    ready_files.append(file_path)
                    del self.pending_files[file_path]
                elif not os.path.exists(file_path):
                    # File was deleted, remove from queue
                    del self.pending_files[file_path]

        # Submit ready files for processing (only if still running)
        for file_path in ready_files:
            if not self._running:
                self.logger.info(
                    f"Monitor shutting down, skipping conversion of {file_path}"
                )
                break
            if self.file_tracker.start_processing(file_path):
                self.logger.info(f"Starting conversion: {file_path}")
                # Submit to thread pool for parallel processing (F8)
                self.executor.submit(self._process_file_sync, file_path)
                # Don't await here to allow parallel processing

    def _process_file_sync(self, file_path: str):
        """Synchronous wrapper for file processing (for thread pool)."""
        try:
            # Check if converter is cancelled before starting
            if self.converter.is_cancelled():
                self.logger.info(f"Converter cancelled, skipping {file_path}")
                self.file_tracker.finish_processing(file_path, success=False)
                return

            # Run the async conversion in a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.converter.convert_file(file_path))
                self.file_tracker.finish_processing(file_path, success=True)
                self.logger.info(f"Successfully converted: {file_path}")
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Failed to convert {file_path}: {e}")
            self.file_tracker.finish_processing(file_path, success=False)

    def scan_existing_files(self):
        """Scan input directory for existing files on startup (NF10)."""
        self.logger.info(f"Scanning existing files in: {self.config.input_dir}")
        try:
            for root, dirs, files in os.walk(self.config.input_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self.is_video_file(file_path):
                        self.queue_file_for_processing(file_path)
            self.logger.info("Completed initial file scan")
        except Exception as e:
            self.logger.error(f"Error during initial file scan: {e}")

    async def start(self):
        """Start the video monitoring system."""
        self._running = True
        self.logger.info("Starting video monitor")

        # Scan for existing files first
        self.scan_existing_files()

        # Setup directory monitoring (F1)
        event_handler = VideoFileHandler(self)
        self.observer.schedule(event_handler, self.config.input_dir, recursive=True)
        self.observer.start()
        self.logger.info(f"Started monitoring: {self.config.input_dir}")

        try:
            # Main processing loop
            while self._running:
                await self.process_pending_files()
                await asyncio.sleep(self.config.polling_interval)
        except asyncio.CancelledError:
            self.logger.info("Monitor cancelled, shutting down...")
        finally:
            # Cancel any ongoing conversions
            self.converter.cancel()
            self.observer.stop()
            self.observer.join()
            self.executor.shutdown(wait=True)
            self.logger.info("Video monitor stopped")
