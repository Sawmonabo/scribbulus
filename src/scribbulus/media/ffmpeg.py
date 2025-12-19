"""FFmpeg discovery and helper functions."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scribbulus.utils.errors import FFmpegNotFoundError, FFprobeError

# Minimum parts in ffmpeg version output: "ffmpeg version X.X.X"
_FFMPEG_VERSION_MIN_PARTS = 3


@dataclass
class FFmpegInfo:
    """Information about the installed FFmpeg."""

    path: Path
    version: str


def find_ffmpeg() -> Path | None:
    """
    Find the ffmpeg executable.

    :returns: Path to ffmpeg if found, None otherwise.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return Path(ffmpeg_path)
    return None


def find_ffprobe() -> Path | None:
    """
    Find the ffprobe executable.

    :returns: Path to ffprobe if found, None otherwise.
    """
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        return Path(ffprobe_path)
    return None


def check_ffmpeg_available() -> bool:
    """
    Check if ffmpeg is available on the system.

    :returns: True if ffmpeg is available, False otherwise.
    """
    return find_ffmpeg() is not None


def check_ffprobe_available() -> bool:
    """
    Check if ffprobe is available on the system.

    :returns: True if ffprobe is available, False otherwise.
    """
    return find_ffprobe() is not None


def get_ffmpeg_version() -> str | None:
    """
    Get the version of ffmpeg.

    :returns: Version string if ffmpeg is found, None otherwise.
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
        if len(parts) >= _FFMPEG_VERSION_MIN_PARTS and parts[0] == "ffmpeg":
            return parts[2]
        return first_line
    except subprocess.CalledProcessError:
        return None


def get_ffmpeg_info() -> FFmpegInfo:
    """
    Get information about the installed FFmpeg.

    :returns: FFmpegInfo with path and version.
    :raises FFmpegNotFoundError: If ffmpeg is not found.
    """
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise FFmpegNotFoundError()

    version = get_ffmpeg_version() or "unknown"
    return FFmpegInfo(path=ffmpeg_path, version=version)


def run_ffprobe(file_path: str | Path) -> dict[str, Any]:
    """
    Run ffprobe on a file and return the JSON output.

    :param file_path: Path to the media file.
    :returns: Parsed JSON output from ffprobe.
    :raises FFmpegNotFoundError: If ffprobe is not found.
    :raises FFprobeError: If ffprobe fails to analyze the file.
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
        data: dict[str, Any] = json.loads(result.stdout)
        return data
    except subprocess.CalledProcessError as e:
        raise FFprobeError(
            e.stderr.strip() or "Unknown error", str(file_path)
        ) from e
    except json.JSONDecodeError as e:
        raise FFprobeError(
            f"Failed to parse ffprobe output: {e}", str(file_path)
        ) from e


def get_audio_duration(file_path: str | Path) -> float:
    """
    Get the duration of an audio/video file in seconds.

    :param file_path: Path to the media file.
    :returns: Duration in seconds.
    :raises FFprobeError: If duration cannot be determined.
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

    :param file_path: Path to the media file.
    :returns: True if the file has an audio stream, False otherwise.
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

    :param file_path: Path to the media file.
    :returns: Dictionary with audio stream info, or None if no audio stream.
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

    :param args: Arguments to pass to ffmpeg (not including 'ffmpeg' itself).
    :param check: Raise exception on non-zero exit code.
    :param capture_output: Capture stdout and stderr.
    :param timeout: Timeout in seconds.
    :returns: CompletedProcess instance.
    :raises FFmpegNotFoundError: If ffmpeg is not found.
    :raises subprocess.CalledProcessError: If check=True and non-zero exit.
    :raises subprocess.TimeoutExpired: If timeout is exceeded.
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
