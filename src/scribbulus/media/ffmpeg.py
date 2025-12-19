"""FFmpeg discovery and helper functions."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scribbulus.utils.errors import FFmpegNotFoundError, FFprobeError


@dataclass
class FFmpegInfo:
    """Information about the installed FFmpeg."""

    path: Path
    version: str


def find_ffmpeg() -> Path | None:
    """
    Find the ffmpeg executable.

    Returns:
        Path to ffmpeg if found, None otherwise.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return Path(ffmpeg_path)
    return None


def find_ffprobe() -> Path | None:
    """
    Find the ffprobe executable.

    Returns:
        Path to ffprobe if found, None otherwise.
    """
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        return Path(ffprobe_path)
    return None


def check_ffmpeg_available() -> bool:
    """
    Check if ffmpeg is available on the system.

    Returns:
        True if ffmpeg is available, False otherwise.
    """
    return find_ffmpeg() is not None


def check_ffprobe_available() -> bool:
    """
    Check if ffprobe is available on the system.

    Returns:
        True if ffprobe is available, False otherwise.
    """
    return find_ffprobe() is not None


def get_ffmpeg_version() -> str | None:
    """
    Get the version of ffmpeg.

    Returns:
        Version string if ffmpeg is found, None otherwise.
    """
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        return None

    try:
        result = subprocess.run(
            [str(ffmpeg_path), "-version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse first line: "ffmpeg version X.X.X ..."
        first_line = result.stdout.split("\n")[0]
        parts = first_line.split()
        if len(parts) >= 3 and parts[0] == "ffmpeg":
            return parts[2]
        return first_line
    except subprocess.CalledProcessError:
        return None


def get_ffmpeg_info() -> FFmpegInfo:
    """
    Get information about the installed FFmpeg.

    Returns:
        FFmpegInfo with path and version.

    Raises:
        FFmpegNotFoundError: If ffmpeg is not found.
    """
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise FFmpegNotFoundError()

    version = get_ffmpeg_version() or "unknown"
    return FFmpegInfo(path=ffmpeg_path, version=version)


def run_ffprobe(file_path: str | Path) -> dict[str, Any]:
    """
    Run ffprobe on a file and return the JSON output.

    Args:
        file_path: Path to the media file.

    Returns:
        Parsed JSON output from ffprobe.

    Raises:
        FFmpegNotFoundError: If ffprobe is not found.
        FFprobeError: If ffprobe fails to analyze the file.
    """
    ffprobe_path = find_ffprobe()
    if not ffprobe_path:
        raise FFmpegNotFoundError("ffprobe not found")

    file_path = Path(file_path)
    if not file_path.exists():
        raise FFprobeError("File not found", str(file_path))

    cmd = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-print_format",
        "json",
        str(file_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise FFprobeError(e.stderr.strip() or "Unknown error", str(file_path)) from e
    except json.JSONDecodeError as e:
        raise FFprobeError(f"Failed to parse ffprobe output: {e}", str(file_path)) from e


def get_audio_duration(file_path: str | Path) -> float:
    """
    Get the duration of an audio/video file in seconds.

    Args:
        file_path: Path to the media file.

    Returns:
        Duration in seconds.

    Raises:
        FFprobeError: If duration cannot be determined.
    """
    probe_data = run_ffprobe(file_path)

    # Try to get duration from format
    if "format" in probe_data and "duration" in probe_data["format"]:
        return float(probe_data["format"]["duration"])

    # Try to get duration from first audio stream
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "audio" and "duration" in stream:
            return float(stream["duration"])

    raise FFprobeError("Could not determine file duration", str(file_path))


def has_audio_stream(file_path: str | Path) -> bool:
    """
    Check if a file has an audio stream.

    Args:
        file_path: Path to the media file.

    Returns:
        True if the file has an audio stream, False otherwise.
    """
    try:
        probe_data = run_ffprobe(file_path)
        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "audio":
                return True
        return False
    except FFprobeError:
        return False


def get_audio_info(file_path: str | Path) -> dict[str, Any] | None:
    """
    Get information about the audio stream in a file.

    Args:
        file_path: Path to the media file.

    Returns:
        Dictionary with audio stream info, or None if no audio stream.
    """
    probe_data = run_ffprobe(file_path)

    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "audio":
            return {
                "codec_name": stream.get("codec_name"),
                "codec_long_name": stream.get("codec_long_name"),
                "sample_rate": int(stream.get("sample_rate", 0)) or None,
                "channels": int(stream.get("channels", 0)) or None,
                "channel_layout": stream.get("channel_layout"),
                "bit_rate": int(stream.get("bit_rate", 0)) or None,
                "duration": float(stream.get("duration", 0)) or None,
            }

    return None


def run_ffmpeg(
    args: list[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run ffmpeg with the given arguments.

    Args:
        args: Arguments to pass to ffmpeg (not including 'ffmpeg' itself).
        check: Raise exception on non-zero exit code.
        capture_output: Capture stdout and stderr.
        timeout: Timeout in seconds.

    Returns:
        CompletedProcess instance.

    Raises:
        FFmpegNotFoundError: If ffmpeg is not found.
        subprocess.CalledProcessError: If check=True and ffmpeg returns non-zero.
        subprocess.TimeoutExpired: If timeout is exceeded.
    """
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise FFmpegNotFoundError()

    cmd = [str(ffmpeg_path), *args]

    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=check,
        timeout=timeout,
    )
