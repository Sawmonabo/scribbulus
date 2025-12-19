"""Tests for FFmpeg discovery and helper module."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from scribbulus.media.ffmpeg import (
    find_ffmpeg,
    find_ffprobe,
    get_audio_duration,
    run_ffmpeg,
    run_ffprobe,
)
from scribbulus.utils.errors import FFmpegNotFoundError, FFprobeError


class TestFindFFmpeg:
    """Test FFmpeg discovery functions."""

    def test_find_ffmpeg_when_available(self):
        """find_ffmpeg should return path when ffmpeg is installed."""
        if shutil.which("ffmpeg"):
            result = find_ffmpeg()
            assert result is not None
            assert "ffmpeg" in str(result).lower()
        else:
            pytest.skip("ffmpeg not installed")

    def test_find_ffprobe_when_available(self):
        """find_ffprobe should return path when ffprobe is installed."""
        if shutil.which("ffprobe"):
            result = find_ffprobe()
            assert result is not None
            assert "ffprobe" in str(result).lower()
        else:
            pytest.skip("ffprobe not installed")

    def test_find_ffmpeg_returns_none_when_not_found(self):
        """find_ffmpeg should return None when ffmpeg is not installed."""
        with patch("shutil.which", return_value=None):
            result = find_ffmpeg()
            assert result is None

    def test_find_ffprobe_returns_none_when_not_found(self):
        """find_ffprobe should return None when ffprobe is not installed."""
        with patch("shutil.which", return_value=None):
            result = find_ffprobe()
            assert result is None


class TestRunFFmpeg:
    """Test run_ffmpeg function."""

    @pytest.mark.skipif(
        not shutil.which("ffmpeg"), reason="ffmpeg not installed"
    )
    def test_run_ffmpeg_version(self):
        """run_ffmpeg should execute ffmpeg commands."""
        result = run_ffmpeg(["-version"], check=True)
        assert result.returncode == 0

    def test_run_ffmpeg_raises_when_not_found(self):
        """run_ffmpeg should raise when ffmpeg is not found."""
        with (
            patch("scribbulus.media.ffmpeg.find_ffmpeg", return_value=None),
            pytest.raises(FFmpegNotFoundError),
        ):
            run_ffmpeg(["-version"])


class TestRunFFprobe:
    """Test run_ffprobe function."""

    def test_run_ffprobe_raises_when_not_found(self):
        """run_ffprobe should raise when ffprobe is not found."""
        with (
            patch("scribbulus.media.ffmpeg.find_ffprobe", return_value=None),
            pytest.raises(FFmpegNotFoundError),
        ):
            run_ffprobe(Path("/fake/file.mp4"))

    @pytest.mark.skipif(
        not shutil.which("ffprobe"), reason="ffprobe not installed"
    )
    def test_run_ffprobe_raises_for_missing_file(self, temp_dir):
        """run_ffprobe should raise FFprobeError for non-existent file."""
        fake_path = temp_dir / "nonexistent.wav"

        with pytest.raises(FFprobeError):
            run_ffprobe(fake_path)


class TestGetAudioDuration:
    """Test get_audio_duration function."""

    @pytest.mark.skipif(
        not shutil.which("ffprobe"), reason="ffprobe not installed"
    )
    def test_get_duration_of_sample_wav(self, sample_wav):
        """get_audio_duration should return correct duration."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV file")

        duration = get_audio_duration(sample_wav)
        # We created a 3-second file
        assert 2.9 <= duration <= 3.1

    @pytest.mark.skipif(
        not shutil.which("ffprobe"), reason="ffprobe not installed"
    )
    def test_get_duration_file_not_found(self, temp_dir):
        """get_audio_duration should raise for non-existent file."""
        fake_path = temp_dir / "nonexistent.wav"

        with pytest.raises(FFprobeError):
            get_audio_duration(fake_path)

    def test_get_duration_parses_ffprobe_output(self):
        """get_audio_duration should parse ffprobe JSON output correctly."""
        mock_probe_data = {"format": {"duration": "123.456"}}

        with patch("scribbulus.media.ffmpeg.run_ffprobe") as mock_ffprobe:
            mock_ffprobe.return_value = mock_probe_data

            duration = get_audio_duration(Path("test.wav"))

            assert duration == 123.456
