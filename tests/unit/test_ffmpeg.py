"""Tests for FFmpeg discovery and helper module."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scribbulus.media.ffmpeg import (
    find_ffmpeg,
    find_ffprobe,
    get_audio_duration,
    run_ffmpeg,
    run_ffprobe,
)
from scribbulus.utils.errors import FFmpegNotFoundError


class TestFindFFmpeg:
    """Test FFmpeg discovery functions."""

    def test_find_ffmpeg_when_available(self):
        """find_ffmpeg should return path when ffmpeg is installed."""
        if shutil.which("ffmpeg"):
            result = find_ffmpeg()
            assert result is not None
            assert "ffmpeg" in result.lower()
        else:
            pytest.skip("ffmpeg not installed")

    def test_find_ffprobe_when_available(self):
        """find_ffprobe should return path when ffprobe is installed."""
        if shutil.which("ffprobe"):
            result = find_ffprobe()
            assert result is not None
            assert "ffprobe" in result.lower()
        else:
            pytest.skip("ffprobe not installed")

    def test_find_ffmpeg_caches_result(self):
        """find_ffmpeg should cache its result."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"

            # Clear any cached value
            import scribbulus.media.ffmpeg as ffmpeg_module

            ffmpeg_module._ffmpeg_path = None

            result1 = find_ffmpeg()
            result2 = find_ffmpeg()

            # Should only call which once due to caching
            assert mock_which.call_count == 1
            assert result1 == result2

    def test_find_ffprobe_caches_result(self):
        """find_ffprobe should cache its result."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffprobe"

            import scribbulus.media.ffmpeg as ffmpeg_module

            ffmpeg_module._ffprobe_path = None

            result1 = find_ffprobe()
            result2 = find_ffprobe()

            assert mock_which.call_count == 1
            assert result1 == result2


class TestRunFFmpeg:
    """Test run_ffmpeg function."""

    @pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
    def test_run_ffmpeg_version(self):
        """run_ffmpeg should execute ffmpeg commands."""
        result = run_ffmpeg(["-version"], check=True)
        assert result.returncode == 0

    def test_run_ffmpeg_raises_when_not_found(self):
        """run_ffmpeg should raise when ffmpeg is not found."""
        with patch("scribbulus.media.ffmpeg.find_ffmpeg", return_value=None):
            with pytest.raises(FFmpegNotFoundError):
                run_ffmpeg(["-version"])


class TestRunFFprobe:
    """Test run_ffprobe function."""

    @pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe not installed")
    def test_run_ffprobe_version(self):
        """run_ffprobe should execute ffprobe commands."""
        result = run_ffprobe(["-version"], check=True)
        assert result.returncode == 0

    def test_run_ffprobe_raises_when_not_found(self):
        """run_ffprobe should raise when ffprobe is not found."""
        with patch("scribbulus.media.ffmpeg.find_ffprobe", return_value=None):
            with pytest.raises(FFmpegNotFoundError):
                run_ffprobe(["-version"])


class TestGetAudioDuration:
    """Test get_audio_duration function."""

    @pytest.mark.skipif(not shutil.which("ffprobe"), reason="ffprobe not installed")
    def test_get_duration_of_sample_wav(self, sample_wav):
        """get_audio_duration should return correct duration."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV file")

        duration = get_audio_duration(sample_wav)
        # We created a 3-second file
        assert 2.9 <= duration <= 3.1

    def test_get_duration_file_not_found(self, temp_dir):
        """get_audio_duration should raise for non-existent file."""
        fake_path = temp_dir / "nonexistent.wav"

        with pytest.raises(FileNotFoundError):
            get_audio_duration(fake_path)

    def test_get_duration_parses_ffprobe_output(self):
        """get_audio_duration should parse ffprobe JSON output correctly."""
        mock_output = json.dumps({"format": {"duration": "123.456"}})

        with patch("scribbulus.media.ffmpeg.run_ffprobe") as mock_ffprobe:
            mock_result = MagicMock()
            mock_result.stdout = mock_output
            mock_ffprobe.return_value = mock_result

            with patch("pathlib.Path.exists", return_value=True):
                duration = get_audio_duration(Path("test.wav"))

            assert duration == 123.456
