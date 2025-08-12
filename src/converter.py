"""Video to audio conversion module."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict

from mutagen.mp3 import MP3
from mutagen.id3 import TIT2, TPE1, TALB, TRCK
from mutagen.flac import FLAC

from .config import Config


class ConversionError(Exception):
    """Raised when video conversion fails."""

    pass


class VideoConverter:
    """Handles video to audio conversion operations."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._cancelled = False  # Cancellation flag

    def cancel(self):
        """Cancel any ongoing conversion operations."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if conversion operations have been cancelled."""
        return self._cancelled

    def extract_metadata_from_filename(self, file_path: str) -> Dict[str, str]:
        """Extract metadata from filename patterns (F16)."""
        filename = Path(file_path).stem
        parent_dir = Path(file_path).parent.name

        metadata = {
            "artist": "Unknown Artist",
            "title": filename,
            "album": parent_dir,
            "track": "1",
        }

        # Try to parse "Artist - Title" pattern
        if " - " in filename:
            parts = filename.split(" - ", 1)
            metadata["artist"] = parts[0].strip()
            metadata["title"] = parts[1].strip()

            # Check if artist part is actually a track number
            if parts[0].strip().isdigit() or (
                len(parts[0].strip()) == 2 and parts[0].strip().startswith("0")
            ):
                metadata["track"] = parts[0].strip()
                metadata["artist"] = "Unknown Artist"
        elif filename.startswith("0") and len(filename) > 2:
            # Handle numbered tracks like "01 Title" or "01. Title"
            metadata["track"] = filename[:2]
            metadata["title"] = filename[2:].lstrip(" -_.")

        return metadata

    def get_output_path(self, input_path: str) -> str:
        """Generate output path maintaining folder structure (F4)."""
        # Get relative path from input directory
        input_path_obj = Path(input_path)
        input_dir_obj = Path(self.config.input_dir)

        try:
            relative_path = input_path_obj.relative_to(input_dir_obj)
        except ValueError:
            # If input file is not under input_dir, use just the filename
            relative_path = input_path_obj.name

        # Change extension and apply prefix/postfix
        output_filename = self.config.get_output_filename(str(relative_path))

        # Construct full output path
        output_dir = Path(self.config.output_dir) / relative_path.parent
        output_path = output_dir / output_filename

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        return str(output_path)

    def get_temp_output_path(self, final_output_path: str) -> str:
        """Generate temporary output path for atomic operations (F11)."""
        import time

        path_obj = Path(final_output_path)
        timestamp = int(time.time() * 1000000)  # microsecond precision
        temp_name = f".tmp_{path_obj.stem}_{timestamp}{path_obj.suffix}"
        return str(path_obj.parent / temp_name)

    async def convert_file(self, input_path: str) -> None:
        """Convert a video file to audio with retries (F12)."""
        for attempt in range(self.config.max_retries + 1):
            if self.is_cancelled():
                self.logger.info(f"Conversion cancelled for {input_path}")
                return

            try:
                await self._convert_file_once(input_path)
                return
            except Exception as e:
                if self.is_cancelled():
                    self.logger.info(f"Conversion cancelled for {input_path}")
                    return

                if attempt < self.config.max_retries:
                    wait_time = self.config.retry_delay * (attempt + 1)
                    self.logger.warning(
                        f"Conversion attempt {attempt + 1} failed for {input_path}: {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    # Use cancellable sleep - avoid asyncio.sleep in threads
                    import time

                    sleep_start = time.time()
                    while (time.time() - sleep_start) < wait_time:
                        if self.is_cancelled():
                            self.logger.info(f"Conversion cancelled for {input_path}")
                            return
                        time.sleep(1)  # Use blocking sleep instead of asyncio.sleep
                else:
                    self.logger.error(
                        f"All {self.config.max_retries + 1} conversion attempts failed for {input_path}: {e}"
                    )
                    raise ConversionError(
                        f"Failed to convert {input_path} after {self.config.max_retries + 1} attempts"
                    )

    async def _convert_file_once(self, input_path: str) -> None:
        """Perform a single conversion attempt."""
        # Check cancellation at the very start
        if self.is_cancelled():
            self.logger.info(f"Conversion cancelled for {input_path}")
            return

        if not os.path.exists(input_path):
            raise ConversionError(f"Input file not found: {input_path}")

        output_path = self.get_output_path(input_path)

        # Skip if output already exists and skip_existing is True (F15)
        if self.config.skip_existing and os.path.exists(output_path):
            self.logger.info(f"Skipping existing file: {output_path}")
            return

        self.logger.info(f"Converting {input_path} to {output_path}")

        # Create temporary output file to avoid partial files
        temp_output = None
        try:
            # Ensure temp file has the correct extension for format detection
            output_ext = Path(output_path).suffix
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=output_ext, dir=Path(output_path).parent
            ) as temp_file:
                temp_output = temp_file.name

            # Build FFmpeg command
            ffmpeg_cmd = self._build_ffmpeg_command(input_path, temp_output)

            # Run FFmpeg conversion
            await self._run_ffmpeg(ffmpeg_cmd)

            # Embed metadata (F16)
            metadata = self.extract_metadata_from_filename(input_path)
            self._embed_metadata(temp_output, metadata)

            # Move temp file to final location atomically
            os.rename(temp_output, output_path)
            temp_output = None  # Prevent cleanup of moved file

            self.logger.info(f"Successfully converted: {output_path}")

        except Exception as e:
            # Clean up temp file on error
            if temp_output and os.path.exists(temp_output):
                try:
                    os.unlink(temp_output)
                except OSError:
                    pass
            raise ConversionError(f"ffmpeg conversion failed: {e}")

    def _build_ffmpeg_command(self, input_path: str, output_path: str) -> list:
        """Build FFmpeg command based on configuration."""
        cmd = ["ffmpeg", "-i", input_path, "-y"]  # -y to overwrite output

        if self.config.output_format == "mp3":
            # MP3 encoding with specified bitrate (F2)
            cmd.extend(["-acodec", "libmp3lame", "-b:a", f"{self.config.mp3_bitrate}k"])
        elif self.config.output_format == "flac":
            # FLAC encoding with specified bit depth (F3)
            cmd.extend(
                ["-acodec", "flac", "-sample_fmt", f"s{self.config.flac_bit_depth}"]
            )
        else:
            raise ConversionError(
                f"Unsupported output format: {self.config.output_format}"
            )

        # Add audio-only flag
        cmd.append("-vn")
        cmd.append(output_path)

        return cmd

    async def _run_ffmpeg(self, cmd: list) -> None:
        """Run FFmpeg command asynchronously."""
        self.logger.debug(f"Running FFmpeg: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                raise ConversionError(f"ffmpeg failed: {error_msg}")

        except FileNotFoundError:
            raise ConversionError(
                "FFmpeg not found. Please ensure FFmpeg is installed."
            )
        except Exception as e:
            raise ConversionError(f"FFmpeg execution failed: {e}")

    def _embed_metadata(self, audio_path: str, metadata: Dict[str, str]) -> None:
        """Embed metadata into audio file based on format."""
        try:
            if self.config.output_format == "mp3":
                self._embed_mp3_metadata(audio_path, metadata)
            elif self.config.output_format == "flac":
                self._embed_flac_metadata(audio_path, metadata)
        except Exception as e:
            # Log warning but don't fail conversion for metadata issues
            self.logger.warning(f"Failed to embed metadata in {audio_path}: {e}")

    def _embed_flac_metadata(self, audio_path: str, metadata: Dict[str, str]) -> None:
        """Embed metadata into FLAC file."""
        audio = FLAC(audio_path)

        # Set FLAC tags
        audio["TITLE"] = metadata["title"]
        audio["ARTIST"] = metadata["artist"]
        audio["ALBUM"] = metadata["album"]
        audio["TRACKNUMBER"] = metadata["track"]

        audio.save()

    def _embed_mp3_metadata(self, audio_path: str, metadata: Dict[str, str]) -> None:
        """Embed metadata into MP3 file."""
        from mutagen.id3 import ID3

        audio = MP3(audio_path, ID3=ID3)

        # Add ID3 tag if it doesn't exist
        if audio.tags is None:
            audio.add_tags()

        # Set ID3v2 tags
        audio.tags.add(TIT2(encoding=3, text=metadata["title"]))  # Title
        audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))  # Artist
        audio.tags.add(TALB(encoding=3, text=metadata["album"]))  # Album
        audio.tags.add(TRCK(encoding=3, text=metadata["track"]))  # Track number

        audio.save()
