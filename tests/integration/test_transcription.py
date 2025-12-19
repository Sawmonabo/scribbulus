"""Integration tests for the full transcription pipeline.

These tests require external dependencies (ffmpeg, models) and may be slow.
They are skipped if dependencies are not available.
"""

from __future__ import annotations

import shutil
from unittest.mock import MagicMock, patch

import pytest

from scribbulus.media.formats import validate_input_file
from scribbulus.transcription.engine import (
    EngineConfig,
    TranscriptionEngine,
    TranscriptionOutput,
    transcribe_file,
)
from scribbulus.utils.deps import (
    is_cuda_available,
    is_faster_whisper_available,
    is_torch_available,
)


def ffmpeg_available() -> bool:
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None


# Skip markers
skip_if_no_ffmpeg = pytest.mark.skipif(
    not ffmpeg_available(),
    reason="ffmpeg not installed",
)

skip_if_no_whisper = pytest.mark.skipif(
    not is_faster_whisper_available(),
    reason="faster-whisper not installed",
)

skip_if_no_torch = pytest.mark.skipif(
    not is_torch_available(),
    reason="torch not installed",
)

skip_if_no_cuda = pytest.mark.skipif(
    not is_cuda_available(),
    reason="CUDA not available",
)

# Integration tests require all dependencies
requires_full_setup = pytest.mark.skipif(
    not (ffmpeg_available() and is_faster_whisper_available()),
    reason="Requires ffmpeg and faster-whisper",
)


class TestMediaValidation:
    """Integration tests for media file validation."""

    @skip_if_no_ffmpeg
    def test_validate_real_video_file(self, sample_video, temp_dir):
        """Should validate a real video file."""
        if sample_video is None:
            pytest.skip("Could not create sample video")

        media_info = validate_input_file(sample_video)

        assert media_info.has_audio is True
        assert media_info.duration > 0

    @skip_if_no_ffmpeg
    def test_validate_real_audio_file(self, sample_wav, temp_dir):
        """Should validate a real audio file."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        media_info = validate_input_file(sample_wav)

        assert media_info.has_audio is True
        assert media_info.duration > 0


class TestAudioPrepPipeline:
    """Integration tests for audio preparation pipeline."""

    @skip_if_no_ffmpeg
    def test_full_video_to_wav_pipeline(self, sample_video, temp_dir):
        """Should extract and convert video to WAV."""
        if sample_video is None:
            pytest.skip("Could not create sample video")

        from scribbulus.media.audio_prep import prepare_for_transcription

        prepared_path, is_temp = prepare_for_transcription(
            sample_video,
            output_dir=temp_dir,
        )

        assert prepared_path.exists()
        assert prepared_path.suffix == ".wav"
        assert is_temp is True

        # Verify the WAV file is valid
        media_info = validate_input_file(prepared_path)
        assert media_info.audio_sample_rate == 16000

    @skip_if_no_ffmpeg
    def test_chunking_pipeline(self, sample_wav, temp_dir):
        """Should chunk audio file correctly."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        from scribbulus.transcription.chunking import (
            AudioChunker,
            ChunkingConfig,
        )

        config = ChunkingConfig(
            chunk_duration_sec=1.0,  # 1 second chunks for 3 second audio
            overlap_sec=0.1,
            temp_dir=temp_dir,
        )
        chunker = AudioChunker(config=config)

        try:
            chunks = list(chunker.chunk_audio(sample_wav))

            assert len(chunks) >= 2  # Should have multiple chunks
            assert all(chunk.path.exists() for chunk in chunks)
        finally:
            chunker.cleanup_all()


class TestTranscriptionEngine:
    """Integration tests for transcription engine.

    Note: These tests are slow as they require model loading.
    They use the smallest model (tiny) to minimize test time.
    """

    @requires_full_setup
    @pytest.mark.slow
    def test_transcribe_silent_audio(self, sample_wav, temp_dir):
        """Should transcribe silent audio (produces minimal output)."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        config = EngineConfig(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            enable_diarization=False,
            enable_chunking=False,
        )

        with TranscriptionEngine(config=config) as engine:
            output = engine.transcribe(sample_wav)

        assert isinstance(output, TranscriptionOutput)
        assert output.duration > 0
        assert output.language is not None
        # Silent audio may produce empty or minimal text

    @requires_full_setup
    @pytest.mark.slow
    def test_transcribe_with_progress_callback(self, sample_wav, temp_dir):
        """Should call progress callback during transcription."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        progress_calls = []

        def progress_callback(stage: str, progress: float) -> None:
            progress_calls.append((stage, progress))

        config = EngineConfig(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            enable_diarization=False,
            enable_chunking=False,
        )

        with TranscriptionEngine(
            config=config,
            progress_callback=progress_callback,
        ) as engine:
            engine.transcribe(sample_wav)

        # Should have received progress updates
        assert len(progress_calls) > 0
        stages = [call[0] for call in progress_calls]
        assert "Validating input" in stages
        assert "Preparing audio" in stages
        assert "Transcribing" in stages

    @requires_full_setup
    @pytest.mark.slow
    def test_transcribe_video_file(self, sample_video, temp_dir):
        """Should transcribe video file by extracting audio."""
        if sample_video is None:
            pytest.skip("Could not create sample video")

        config = EngineConfig(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            enable_diarization=False,
            enable_chunking=False,
        )

        with TranscriptionEngine(config=config) as engine:
            output = engine.transcribe(sample_video)

        assert isinstance(output, TranscriptionOutput)
        assert output.duration > 0


class TestTranscribeFileConvenienceFunction:
    """Tests for the transcribe_file convenience function."""

    @requires_full_setup
    @pytest.mark.slow
    def test_transcribe_file_basic(self, sample_wav):
        """Should transcribe using convenience function."""
        if sample_wav is None:
            pytest.skip("Could not create sample WAV")

        output = transcribe_file(
            sample_wav,
            model_size="tiny",
            enable_diarization=False,
        )

        assert isinstance(output, TranscriptionOutput)
        assert output.duration > 0


class TestTranscriptionOutput:
    """Tests for TranscriptionOutput formatting."""

    def test_format_transcript_basic(self):
        """Should format transcript without speakers."""
        from scribbulus.transcription.whisper_backend import Segment

        segments = [
            Segment(start=0.0, end=2.0, text="Hello world."),
            Segment(start=2.0, end=4.0, text="How are you?"),
        ]

        output = TranscriptionOutput(
            text="Hello world. How are you?",
            language="en",
            duration=4.0,
            segments=segments,
        )

        formatted = output.format_transcript(
            include_speakers=False,
            include_timestamps=False,
        )

        assert "Hello world" in formatted
        assert "How are you" in formatted

    def test_format_transcript_with_timestamps(self):
        """Should include timestamps when requested."""
        from scribbulus.transcription.whisper_backend import Segment

        segments = [
            Segment(start=65.0, end=67.0, text="One minute in."),
        ]

        output = TranscriptionOutput(
            text="One minute in.",
            language="en",
            duration=67.0,
            segments=segments,
        )

        formatted = output.format_transcript(
            include_speakers=False,
            include_timestamps=True,
        )

        assert "[01:05]" in formatted
        assert "One minute in" in formatted


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    def test_engine_cleanup_on_error(self, temp_dir):
        """Engine should clean up resources on error."""
        config = EngineConfig(
            model_size="tiny",
            enable_diarization=False,
        )

        engine = TranscriptionEngine(config=config)

        # Setup test file
        dummy_file = temp_dir / "test.wav"
        dummy_file.write_bytes(b"fake")

        # Simulate an error during transcription
        with (
            patch.object(
                engine,
                "_transcribe_full",
                side_effect=RuntimeError("Test error"),
            ),
            patch(
                "scribbulus.transcription.engine.validate_input_file"
            ) as mock_validate,
            patch(
                "scribbulus.transcription.engine.prepare_for_transcription"
            ) as mock_prep,
        ):
            mock_info = MagicMock()
            mock_info.duration = 10.0
            mock_validate.return_value = mock_info
            mock_prep.return_value = (dummy_file, False)

            with pytest.raises(RuntimeError, match="Test error"):
                engine.transcribe(dummy_file)

        # Engine should have attempted cleanup
        assert engine._transcriber is None
        assert engine._diarizer is None

    @skip_if_no_ffmpeg
    def test_handles_corrupt_file_gracefully(self, temp_dir):
        """Should handle corrupt files with clear error."""
        corrupt_file = temp_dir / "corrupt.mp4"
        corrupt_file.write_bytes(b"not a real video file")

        from scribbulus.utils.errors import UnsupportedFormatError

        # The validation should fail for corrupt files
        with pytest.raises((UnsupportedFormatError, Exception)):
            validate_input_file(corrupt_file)
