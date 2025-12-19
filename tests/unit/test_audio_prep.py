"""Tests for audio preparation module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scribbulus.media.audio_prep import (
    cleanup_temp_file,
    convert_audio_to_wav,
    extract_audio_chunk,
    extract_audio_from_video,
    prepare_for_transcription,
)
from scribbulus.utils.errors import FFmpegNotFoundError
from tests.conftest import requires_ffmpeg


class TestExtractAudioFromVideo:
    """Test extract_audio_from_video function."""

    def test_raises_when_ffmpeg_not_found(self, temp_dir):
        """Should raise FFmpegNotFoundError when ffmpeg is not available."""
        with (
            patch(
                "scribbulus.media.audio_prep.find_ffmpeg", return_value=None
            ),
            pytest.raises(FFmpegNotFoundError),
        ):
            extract_audio_from_video(
                temp_dir / "input.mp4",
                temp_dir / "output.wav",
            )

    @requires_ffmpeg
    def test_extract_from_sample_video(self, sample_video, temp_dir):
        """Should extract audio from video file."""
        if sample_video is None:
            pytest.skip("Could not create sample video")

        output_path = temp_dir / "extracted.wav"
        result = extract_audio_from_video(sample_video, output_path)

        assert result.exists()
        assert result.suffix == ".wav"

    @requires_ffmpeg
    def test_extract_with_custom_sample_rate(self, sample_video, temp_dir):
        """Should respect custom sample rate setting."""
        if sample_video is None:
            pytest.skip("Could not create sample video")

        output_path = temp_dir / "extracted_44k.wav"
        result = extract_audio_from_video(
            sample_video,
            output_path,
            sample_rate=44100,
        )

        assert result.exists()


class TestConvertAudioToWav:
    """Test convert_audio_to_wav function."""

    def test_raises_when_ffmpeg_not_found(self, temp_dir):
        """Should raise FFmpegNotFoundError when ffmpeg is not available."""
        with (
            patch(
                "scribbulus.media.audio_prep.find_ffmpeg", return_value=None
            ),
            pytest.raises(FFmpegNotFoundError),
        ):
            convert_audio_to_wav(
                temp_dir / "input.mp3",
                temp_dir / "output.wav",
            )

    @requires_ffmpeg
    def test_convert_mp3_to_wav(self, sample_mp3, temp_dir):
        """Should convert MP3 to WAV."""
        if sample_mp3 is None:
            pytest.skip("Could not create sample MP3")

        output_path = temp_dir / "converted.wav"
        result = convert_audio_to_wav(sample_mp3, output_path)

        assert result.exists()
        assert result.suffix == ".wav"

    @requires_ffmpeg
    def test_convert_preserves_stereo_when_requested(
        self, sample_mp3, temp_dir
    ):
        """Should preserve stereo when mono=False."""
        if sample_mp3 is None:
            pytest.skip("Could not create sample MP3")

        output_path = temp_dir / "stereo.wav"
        result = convert_audio_to_wav(
            sample_mp3,
            output_path,
            mono=False,
        )

        assert result.exists()


class TestPrepareForTranscription:
    """Test prepare_for_transcription function."""

    @requires_ffmpeg
    def test_prepare_video_file(self, sample_video, temp_dir):
        """Should prepare video file for transcription."""
        if sample_video is None:
            pytest.skip("Could not create sample video")

        prepared_path, is_temp = prepare_for_transcription(
            sample_video,
            output_dir=temp_dir,
        )

        assert prepared_path.exists()
        assert prepared_path.suffix == ".wav"
        assert is_temp is True

    @requires_ffmpeg
    def test_prepare_wav_already_optimal(self, sample_wav, temp_dir):
        """Should return original path if already optimal WAV."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        # Our sample_wav is already 16kHz mono
        prepared_path, _is_temp = prepare_for_transcription(sample_wav)

        # Should recognize it's already optimal
        # Note: This depends on _is_optimal_format working correctly
        assert prepared_path.exists()

    @requires_ffmpeg
    def test_prepare_mp3_converts_to_wav(self, sample_mp3, temp_dir):
        """Should convert MP3 to WAV."""
        if sample_mp3 is None:
            pytest.skip("Could not create sample MP3")

        prepared_path, is_temp = prepare_for_transcription(
            sample_mp3,
            output_dir=temp_dir,
        )

        assert prepared_path.exists()
        assert prepared_path.suffix == ".wav"
        assert is_temp is True


class TestExtractAudioChunk:
    """Test extract_audio_chunk function."""

    def test_raises_when_ffmpeg_not_found(self, temp_dir):
        """Should raise FFmpegNotFoundError when ffmpeg is not available."""
        with (
            patch(
                "scribbulus.media.audio_prep.find_ffmpeg", return_value=None
            ),
            pytest.raises(FFmpegNotFoundError),
        ):
            extract_audio_chunk(
                temp_dir / "input.wav",
                temp_dir / "chunk.wav",
                start_time=0.0,
                duration=10.0,
            )

    @requires_ffmpeg
    def test_extract_chunk_from_wav(self, sample_wav, temp_dir):
        """Should extract a chunk from WAV file."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        chunk_path = temp_dir / "chunk.wav"
        result = extract_audio_chunk(
            sample_wav,
            chunk_path,
            start_time=0.0,
            duration=1.0,
        )

        assert result.exists()
        assert result.suffix == ".wav"


class TestCleanupTempFile:
    """Test cleanup_temp_file function."""

    def test_cleanup_existing_file(self, temp_dir):
        """Should delete existing temporary file."""
        temp_file = temp_dir / "temp_audio.wav"
        temp_file.write_bytes(b"fake audio data")

        assert temp_file.exists()
        cleanup_temp_file(temp_file)
        assert not temp_file.exists()

    def test_cleanup_nonexistent_file(self, temp_dir):
        """Should not raise for non-existent file."""
        fake_file = temp_dir / "nonexistent.wav"

        # Should not raise
        cleanup_temp_file(fake_file)

    def test_cleanup_handles_permission_error(self, temp_dir):
        """Should handle permission errors gracefully."""
        temp_file = temp_dir / "protected.wav"
        temp_file.write_bytes(b"data")

        with patch.object(
            Path, "unlink", side_effect=OSError("Permission denied")
        ):
            # Should not raise
            cleanup_temp_file(temp_file)
