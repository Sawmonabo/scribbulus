"""Format detection and validation for media files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scribbulus.media.ffmpeg import run_ffprobe
from scribbulus.utils.errors import (
    FFprobeError,
    NoAudioStreamError,
    UnsupportedFormatError,
)

# Supported file extensions
SUPPORTED_VIDEO: set[str] = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".flv",
    ".wmv",
}
SUPPORTED_AUDIO: set[str] = {
    ".wav",
    ".mp3",
    ".m4a",
    ".flac",
    ".ogg",
    ".aac",
    ".wma",
    ".opus",
}
SUPPORTED_FORMATS: set[str] = SUPPORTED_VIDEO | SUPPORTED_AUDIO

# Bytes per kilobyte for file size formatting
_BYTES_PER_KB = 1024

FileType = Literal["video", "audio"]


@dataclass
class MediaInfo:
    """Information about a media file."""

    path: Path
    format_name: str
    duration: float
    file_size: int
    has_audio: bool
    has_video: bool
    audio_codec: str | None = None
    audio_channels: int | None = None
    audio_sample_rate: int | None = None
    audio_bit_rate: int | None = None
    video_codec: str | None = None

    @property
    def file_type(self) -> FileType | None:
        """Get the file type (video or audio)."""
        if self.has_video:
            return "video"
        if self.has_audio:
            return "audio"
        return None

    @property
    def duration_formatted(self) -> str:
        """Get duration in HH:MM:SS format."""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


def get_file_extension(file_path: str | Path) -> str:
    """
    Get the lowercase file extension.

    :param file_path: Path to the file.
    :returns: Lowercase file extension including the dot (e.g., ".mp4").
    """
    return Path(file_path).suffix.lower()


def is_supported(file_path: str | Path) -> bool:
    """
    Check if a file format is supported.

    :param file_path: Path to the file.
    :returns: True if the format is supported, False otherwise.
    """
    ext = get_file_extension(file_path)
    return ext in SUPPORTED_FORMATS


def is_video_format(file_path: str | Path) -> bool:
    """
    Check if a file is a video format (by extension).

    :param file_path: Path to the file.
    :returns: True if the file has a video extension.
    """
    ext = get_file_extension(file_path)
    return ext in SUPPORTED_VIDEO


def is_audio_format(file_path: str | Path) -> bool:
    """
    Check if a file is an audio format (by extension).

    :param file_path: Path to the file.
    :returns: True if the file has an audio extension.
    """
    ext = get_file_extension(file_path)
    return ext in SUPPORTED_AUDIO


def get_file_type(file_path: str | Path) -> FileType | None:
    """
    Get the file type based on extension.

    :param file_path: Path to the file.
    :returns: "video", "audio", or None if not supported.
    """
    ext = get_file_extension(file_path)
    if ext in SUPPORTED_VIDEO:
        return "video"
    if ext in SUPPORTED_AUDIO:
        return "audio"
    return None


def probe_media_file(file_path: str | Path) -> MediaInfo:
    """
    Probe a media file and return detailed information.

    :param file_path: Path to the media file.
    :returns: MediaInfo with file details.
    :raises UnsupportedFormatError: If the file format is not supported.
    :raises FFprobeError: If ffprobe fails to analyze the file.
    """
    file_path = Path(file_path)

    # Check extension first
    if not is_supported(file_path):
        raise UnsupportedFormatError(str(file_path))

    # Get file size
    file_size = file_path.stat().st_size

    # Probe with ffprobe
    try:
        probe_data = run_ffprobe(file_path)
    except FFprobeError as e:
        raise UnsupportedFormatError(str(file_path), str(e)) from e

    # Extract format info
    format_info = probe_data.get("format", {})
    format_name = format_info.get("format_name", "unknown")
    duration = float(format_info.get("duration", 0))

    # Analyze streams
    streams = probe_data.get("streams", [])
    has_audio = False
    has_video = False
    audio_codec = None
    audio_channels = None
    audio_sample_rate = None
    audio_bit_rate = None
    video_codec = None

    for stream in streams:
        codec_type = stream.get("codec_type")

        if codec_type == "audio" and not has_audio:
            has_audio = True
            audio_codec = stream.get("codec_name")
            audio_channels = int(stream.get("channels", 0)) or None
            audio_sample_rate = int(stream.get("sample_rate", 0)) or None
            audio_bit_rate = int(stream.get("bit_rate", 0)) or None

            # Get duration from audio stream if format duration is missing
            if duration == 0 and "duration" in stream:
                duration = float(stream["duration"])

        elif codec_type == "video" and not has_video:
            has_video = True
            video_codec = stream.get("codec_name")

    return MediaInfo(
        path=file_path,
        format_name=format_name,
        duration=duration,
        file_size=file_size,
        has_audio=has_audio,
        has_video=has_video,
        audio_codec=audio_codec,
        audio_channels=audio_channels,
        audio_sample_rate=audio_sample_rate,
        audio_bit_rate=audio_bit_rate,
        video_codec=video_codec,
    )


def validate_input_file(file_path: str | Path) -> MediaInfo:
    """
    Validate an input file for transcription.

    :param file_path: Path to the input file.
    :returns: MediaInfo if the file is valid.
    :raises FileNotFoundError: If the file doesn't exist.
    :raises UnsupportedFormatError: If the format is not supported.
    :raises NoAudioStreamError: If the file has no audio.
    """
    file_path = Path(file_path)

    # Check file exists
    if not file_path.exists():
        from scribbulus.utils.errors import (
            FileNotFoundError,
        )

        raise FileNotFoundError(str(file_path))

    # Probe the file
    media_info = probe_media_file(file_path)

    # Check for audio
    if not media_info.has_audio:
        raise NoAudioStreamError(str(file_path))

    return media_info


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    :param size_bytes: Size in bytes.
    :returns: Human-readable size string.
    """
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < _BYTES_PER_KB:
            return f"{size:.1f} {unit}"
        size /= _BYTES_PER_KB
    return f"{size:.1f} PB"
