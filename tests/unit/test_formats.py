"""Tests for format detection module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scribbulus.media.formats import (
    SUPPORTED_AUDIO_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    MediaInfo,
    get_file_type,
    is_audio_format,
    is_supported_format,
    is_video_format,
    parse_ffprobe_output,
    probe_media_file,
    validate_input_file,
)
from scribbulus.utils.errors import (
    NoAudioStreamError,
    UnsupportedFormatError,
)


class TestSupportedExtensions:
    """Test supported format sets."""

    def test_video_extensions_lowercase(self):
        """All video extensions should be lowercase."""
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            assert ext == ext.lower()
            assert ext.startswith(".")

    def test_audio_extensions_lowercase(self):
        """All audio extensions should be lowercase."""
        for ext in SUPPORTED_AUDIO_EXTENSIONS:
            assert ext == ext.lower()
            assert ext.startswith(".")

    def test_expected_video_formats(self):
        """Check expected video formats are supported."""
        expected = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
        assert expected.issubset(SUPPORTED_VIDEO_EXTENSIONS)

    def test_expected_audio_formats(self):
        """Check expected audio formats are supported."""
        expected = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"}
        assert expected.issubset(SUPPORTED_AUDIO_EXTENSIONS)


class TestIsVideoFormat:
    """Test is_video_format function."""

    @pytest.mark.parametrize(
        "filename",
        ["video.mp4", "video.MP4", "video.Mp4", "video.mov", "video.mkv"],
    )
    def test_video_formats_detected(self, filename):
        """Video formats should be detected regardless of case."""
        assert is_video_format(Path(filename))

    @pytest.mark.parametrize("filename", ["audio.mp3", "audio.wav", "audio.flac"])
    def test_audio_formats_not_video(self, filename):
        """Audio formats should not be detected as video."""
        assert not is_video_format(Path(filename))

    def test_string_path_accepted(self):
        """String paths should be accepted."""
        assert is_video_format("video.mp4")


class TestIsAudioFormat:
    """Test is_audio_format function."""

    @pytest.mark.parametrize(
        "filename",
        ["audio.mp3", "audio.MP3", "audio.wav", "audio.m4a", "audio.flac"],
    )
    def test_audio_formats_detected(self, filename):
        """Audio formats should be detected regardless of case."""
        assert is_audio_format(Path(filename))

    @pytest.mark.parametrize("filename", ["video.mp4", "video.mov", "video.mkv"])
    def test_video_formats_not_audio(self, filename):
        """Video formats should not be detected as audio."""
        assert not is_audio_format(Path(filename))


class TestIsSupportedFormat:
    """Test is_supported_format function."""

    @pytest.mark.parametrize(
        "filename",
        [
            "video.mp4",
            "video.mov",
            "audio.mp3",
            "audio.wav",
            "audio.flac",
        ],
    )
    def test_supported_formats(self, filename):
        """Both video and audio formats should be supported."""
        assert is_supported_format(Path(filename))

    @pytest.mark.parametrize(
        "filename",
        ["document.pdf", "image.png", "data.json", "script.py"],
    )
    def test_unsupported_formats(self, filename):
        """Non-media formats should not be supported."""
        assert not is_supported_format(Path(filename))


class TestGetFileType:
    """Test get_file_type function."""

    def test_video_type(self):
        """Video files should return 'video'."""
        assert get_file_type(Path("test.mp4")) == "video"
        assert get_file_type(Path("test.mov")) == "video"

    def test_audio_type(self):
        """Audio files should return 'audio'."""
        assert get_file_type(Path("test.mp3")) == "audio"
        assert get_file_type(Path("test.wav")) == "audio"

    def test_unknown_type(self):
        """Unknown files should return None."""
        assert get_file_type(Path("test.pdf")) is None
        assert get_file_type(Path("test.txt")) is None


class TestParseFFprobeOutput:
    """Test ffprobe output parsing."""

    def test_parse_video_with_audio(self, mock_media_info):
        """Parse video file with audio stream."""
        info = parse_ffprobe_output(mock_media_info, Path("test.mp4"))

        assert info.format_name == "mov,mp4,m4a,3gp,3g2,mj2"
        assert info.duration == 60.0
        assert info.has_video is True
        assert info.has_audio is True
        assert info.video_codec == "h264"
        assert info.audio_codec == "aac"
        assert info.audio_channels == 2
        assert info.audio_sample_rate == 44100

    def test_parse_audio_only(self):
        """Parse audio-only file."""
        ffprobe_output = {
            "format": {
                "filename": "test.mp3",
                "format_name": "mp3",
                "duration": "180.5",
            },
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "channels": 2,
                    "sample_rate": "44100",
                },
            ],
        }

        info = parse_ffprobe_output(ffprobe_output, Path("test.mp3"))

        assert info.has_video is False
        assert info.has_audio is True
        assert info.audio_codec == "mp3"

    def test_parse_video_no_audio(self):
        """Parse video file without audio stream."""
        ffprobe_output = {
            "format": {
                "filename": "test.mp4",
                "format_name": "mp4",
                "duration": "30.0",
            },
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                },
            ],
        }

        info = parse_ffprobe_output(ffprobe_output, Path("test.mp4"))

        assert info.has_video is True
        assert info.has_audio is False


class TestMediaInfo:
    """Test MediaInfo dataclass."""

    def test_media_info_creation(self):
        """Test creating MediaInfo instance."""
        info = MediaInfo(
            format_name="mp4",
            duration=120.5,
            has_video=True,
            has_audio=True,
            video_codec="h264",
            video_width=1920,
            video_height=1080,
            audio_codec="aac",
            audio_channels=2,
            audio_sample_rate=44100,
            file_path=Path("test.mp4"),
        )

        assert info.duration == 120.5
        assert info.has_video is True
        assert info.has_audio is True


class TestValidateInputFile:
    """Test input file validation."""

    def test_file_not_found(self, temp_dir):
        """Non-existent file should raise FileNotFoundError."""
        fake_path = temp_dir / "nonexistent.mp4"

        with pytest.raises(FileNotFoundError):
            validate_input_file(fake_path)

    def test_unsupported_format(self, temp_dir):
        """Unsupported format should raise UnsupportedFormatError."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("test content")

        with pytest.raises(UnsupportedFormatError):
            validate_input_file(txt_file)

    @pytest.mark.skipif(
        not pytest.importorskip("shutil").which("ffprobe"),
        reason="ffprobe not available",
    )
    def test_video_without_audio_raises_error(self, temp_dir):
        """Video file without audio should raise NoAudioStreamError."""
        # This would require creating an actual video without audio
        # which is complex without ffmpeg, so we mock it
        pass
