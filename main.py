#!/usr/bin/env python3
"""
vidaud - Video to Audio Converter
Monitors directories for video files and converts them to audio formats.
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

from src.config import Config
from src.monitor import VideoMonitor
from src.health_server import HealthServer


def setup_logging(config: Config) -> None:
    """Setup logging configuration based on environment settings."""
    log_level = getattr(logging, config.log_level.upper())

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set specific loggers
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {config.log_level} level")


async def main():
    """Main application entry point."""
    try:
        # Load configuration
        config = Config()
        setup_logging(config)

        logger = logging.getLogger(__name__)
        logger.info("Starting vidaud video-to-audio converter")
        logger.info(f"Input directory: {config.input_dir}")
        logger.info(f"Output directory: {config.output_dir}")
        logger.info(f"Output format: {config.output_format}")
        logger.info(f"Parallel jobs: {config.max_parallel_jobs}")

        # Create output directory if it doesn't exist
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

        # Start health server
        health_server = HealthServer(config.health_port)
        health_task = asyncio.create_task(health_server.start())

        # Start video monitor
        monitor = VideoMonitor(config)
        monitor_task = asyncio.create_task(monitor.start())

        # Setup signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully...")
            monitor_task.cancel()
            health_task.cancel()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Wait for tasks
        await asyncio.gather(monitor_task, health_task, return_exceptions=True)

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
