"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


def ffmpeg_available() -> bool:
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None


def cuda_available() -> bool:
    """Check if CUDA is available."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


# Skip markers
skip_if_no_ffmpeg = pytest.mark.skipif(
    not ffmpeg_available(),
    reason="ffmpeg not installed",
)

skip_if_no_cuda = pytest.mark.skipif(
    not cuda_available(),
    reason="CUDA not available",
)

requires_ffmpeg = pytest.mark.skipif(
    not ffmpeg_available(),
    reason="Test requires ffmpeg",
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory(prefix="scribbulus_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_wav(temp_dir: Path) -> Path | None:
    """Create a sample WAV file using ffmpeg (if available)."""
    if not ffmpeg_available():
        return None

    wav_path = temp_dir / "test_audio.wav"

    # Generate 3 seconds of silence as a test audio file
    # Using lavfi filter to generate silence
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=16000:cl=mono",
        "-t",
        "3",
        "-c:a",
        "pcm_s16le",
        str(wav_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
        )
        return wav_path
    except subprocess.CalledProcessError:
        return None


@pytest.fixture
def sample_mp3(temp_dir: Path) -> Path | None:
    """Create a sample MP3 file using ffmpeg (if available)."""
    if not ffmpeg_available():
        return None

    mp3_path = temp_dir / "test_audio.mp3"

    # Generate 3 seconds of silence as MP3
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=stereo",
        "-t",
        "3",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        str(mp3_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
        )
        return mp3_path
    except subprocess.CalledProcessError:
        return None


@pytest.fixture
def sample_video(temp_dir: Path) -> Path | None:
    """Create a sample MP4 video file using ffmpeg (if available)."""
    if not ffmpeg_available():
        return None

    mp4_path = temp_dir / "test_video.mp4"

    # Generate 3 seconds of black video with silence
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=320x240:r=30",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=stereo",
        "-t",
        "3",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(mp4_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
        )
        return mp4_path
    except subprocess.CalledProcessError:
        return None


@pytest.fixture
def mock_media_info() -> dict:
    """Return mock media info for testing."""
    return {
        "format": {
            "filename": "test.mp4",
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
            "duration": "60.0",
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "channels": 2,
                "sample_rate": "44100",
            },
        ],
    }
