"""Audio preparation and extraction for transcription."""

from __future__ import annotations

import atexit
import os
import signal
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from scribbulus.media.ffmpeg import find_ffmpeg, get_audio_duration, run_ffmpeg
from scribbulus.media.formats import MediaInfo, is_video_format, probe_media_file
from scribbulus.utils.errors import AudioExtractionError, FFmpegNotFoundError

if TYPE_CHECKING:
    from collections.abc import Callable

# Track temp files for cleanup
_temp_files: list[Path] = []


def _cleanup_temp_files() -> None:
    """Clean up any remaining temp files."""
    for temp_file in _temp_files:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except OSError:
            pass  # Best effort cleanup


# Register cleanup on exit
atexit.register(_cleanup_temp_files)


def _register_temp_file(path: Path) -> None:
    """Register a temp file for cleanup."""
    _temp_files.append(path)


def _unregister_temp_file(path: Path) -> None:
    """Unregister a temp file after successful processing."""
    if path in _temp_files:
        _temp_files.remove(path)


def extract_audio_from_video(
    input_path: str | Path,
    output_path: str | Path,
    *,
    sample_rate: int = 16000,
    mono: bool = True,
    overwrite: bool = True,
) -> Path:
    """
    Extract audio from a video file.

    Args:
        input_path: Path to the input video file.
        output_path: Path for the output audio file.
        sample_rate: Target sample rate (default: 16000 Hz for STT).
        mono: Convert to mono (default: True for STT).
        overwrite: Overwrite existing output file.

    Returns:
        Path to the extracted audio file.

    Raises:
        FFmpegNotFoundError: If ffmpeg is not found.
        AudioExtractionError: If extraction fails.
    """
    if not find_ffmpeg():
        raise FFmpegNotFoundError()

    input_path = Path(input_path)
    output_path = Path(output_path)

    # Build ffmpeg arguments
    args = [
        "-fflags",
        "+genpts",  # Handle variable frame rate (iPhone videos)
        "-i",
        str(input_path),
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",  # 16-bit PCM
        "-ar",
        str(sample_rate),  # Sample rate
    ]

    if mono:
        args.extend(["-ac", "1"])  # Mono

    if overwrite:
        args.insert(0, "-y")  # Overwrite

    args.append(str(output_path))

    try:
        result = run_ffmpeg(args, check=True)
    except Exception as e:
        raise AudioExtractionError(str(e), str(input_path)) from e

    if not output_path.exists():
        raise AudioExtractionError("Output file was not created", str(input_path))

    return output_path


def convert_audio_to_wav(
    input_path: str | Path,
    output_path: str | Path,
    *,
    sample_rate: int = 16000,
    mono: bool = True,
    overwrite: bool = True,
) -> Path:
    """
    Convert any audio file to WAV format optimized for STT.

    Args:
        input_path: Path to the input audio file.
        output_path: Path for the output WAV file.
        sample_rate: Target sample rate (default: 16000 Hz).
        mono: Convert to mono (default: True).
        overwrite: Overwrite existing output file.

    Returns:
        Path to the converted WAV file.

    Raises:
        FFmpegNotFoundError: If ffmpeg is not found.
        AudioExtractionError: If conversion fails.
    """
    if not find_ffmpeg():
        raise FFmpegNotFoundError()

    input_path = Path(input_path)
    output_path = Path(output_path)

    # Build ffmpeg arguments
    args = [
        "-i",
        str(input_path),
        "-vn",  # No video (in case input is video)
        "-acodec",
        "pcm_s16le",  # 16-bit PCM
        "-ar",
        str(sample_rate),  # Sample rate
    ]

    if mono:
        args.extend(["-ac", "1"])  # Mono

    if overwrite:
        args.insert(0, "-y")  # Overwrite

    args.append(str(output_path))

    try:
        result = run_ffmpeg(args, check=True)
    except Exception as e:
        raise AudioExtractionError(str(e), str(input_path)) from e

    if not output_path.exists():
        raise AudioExtractionError("Output file was not created", str(input_path))

    return output_path


def prepare_for_transcription(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    sample_rate: int = 16000,
    mono: bool = True,
) -> tuple[Path, bool]:
    """
    Prepare any supported file for transcription.

    Converts the input to 16kHz mono WAV format if needed.

    Args:
        input_path: Path to the input file (audio or video).
        output_dir: Directory for temp files (default: system temp).
        sample_rate: Target sample rate (default: 16000 Hz).
        mono: Convert to mono (default: True).

    Returns:
        Tuple of (prepared_audio_path, is_temporary).
        If is_temporary is True, the caller should delete the file when done.

    Raises:
        FFmpegNotFoundError: If ffmpeg is not found.
        AudioExtractionError: If preparation fails.
    """
    input_path = Path(input_path)

    # Determine output directory
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir())
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Check if input is already optimal format
    if _is_optimal_format(input_path, sample_rate, mono):
        return input_path, False

    # Create temp output file
    temp_name = f"scribbulus_{input_path.stem}_{os.getpid()}.wav"
    output_path = output_dir / temp_name

    # Register for cleanup
    _register_temp_file(output_path)

    # Extract/convert to WAV
    if is_video_format(input_path):
        extract_audio_from_video(
            input_path,
            output_path,
            sample_rate=sample_rate,
            mono=mono,
        )
    else:
        convert_audio_to_wav(
            input_path,
            output_path,
            sample_rate=sample_rate,
            mono=mono,
        )

    return output_path, True


def _is_optimal_format(
    file_path: Path,
    target_sample_rate: int,
    mono: bool,
) -> bool:
    """
    Check if a file is already in optimal format for transcription.

    Returns True only if the file is:
    - WAV format
    - Correct sample rate
    - Mono (if mono=True)
    """
    if file_path.suffix.lower() != ".wav":
        return False

    try:
        media_info = probe_media_file(file_path)

        # Check sample rate
        if media_info.audio_sample_rate != target_sample_rate:
            return False

        # Check channels
        if mono and media_info.audio_channels != 1:
            return False

        return True
    except Exception:
        return False


def extract_audio_chunk(
    input_path: str | Path,
    output_path: str | Path,
    start_time: float,
    duration: float,
    *,
    sample_rate: int = 16000,
    mono: bool = True,
) -> Path:
    """
    Extract a chunk of audio from a file.

    Uses seeking before input for memory-efficient extraction.

    Args:
        input_path: Path to the input file.
        output_path: Path for the output chunk.
        start_time: Start time in seconds.
        duration: Duration in seconds.
        sample_rate: Target sample rate.
        mono: Convert to mono.

    Returns:
        Path to the extracted chunk.

    Raises:
        AudioExtractionError: If extraction fails.
    """
    if not find_ffmpeg():
        raise FFmpegNotFoundError()

    input_path = Path(input_path)
    output_path = Path(output_path)

    # Build ffmpeg arguments
    # Note: -ss before -i enables fast seeking without decoding
    args = [
        "-y",  # Overwrite
        "-ss",
        str(start_time),  # Seek position (before input for fast seek)
        "-i",
        str(input_path),
        "-t",
        str(duration),  # Duration
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",  # 16-bit PCM
        "-ar",
        str(sample_rate),
    ]

    if mono:
        args.extend(["-ac", "1"])

    args.append(str(output_path))

    try:
        run_ffmpeg(args, check=True)
    except Exception as e:
        raise AudioExtractionError(
            f"Failed to extract chunk at {start_time}s: {e}",
            str(input_path),
        ) from e

    if not output_path.exists():
        raise AudioExtractionError(
            f"Chunk file was not created at {start_time}s",
            str(input_path),
        )

    return output_path


def cleanup_temp_file(file_path: Path) -> None:
    """
    Clean up a temporary file.

    Args:
        file_path: Path to the file to delete.
    """
    try:
        if file_path.exists():
            file_path.unlink()
        _unregister_temp_file(file_path)
    except OSError:
        pass  # Best effort cleanup
