"""Transcription engine - orchestrates the full transcription pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING

from scribbulus.media.audio_prep import (
    cleanup_temp_file,
    prepare_for_transcription,
)
from scribbulus.media.formats import MediaInfo, validate_input_file
from scribbulus.transcription.chunking import (
    AudioChunk,
    AudioChunker,
    ChunkingConfig,
    merge_chunk_segments,
    merge_transcription_text,
)
from scribbulus.transcription.diarization import (
    SpeakerDiarizer,
    SpeakerSegment,
    format_diarized_transcript,
)
from scribbulus.transcription.whisper_backend import (
    Segment,
    TranscriptionConfig,
    TranscriptionResult,
    WhisperTranscriber,
)
from scribbulus.utils.deps import cleanup_gpu_memory
from scribbulus.utils.formatter import format_simple_segments
from scribbulus.utils.types import (
    ComputeType,
    DeviceType,
    ModelSize,
    ProgressCallback,
)

if TYPE_CHECKING:
    pass


@dataclass
class EngineConfig:
    """Configuration for the transcription engine."""

    # Model settings
    model_size: ModelSize = "large-v3-turbo"
    device: DeviceType = "auto"
    compute_type: ComputeType | None = None

    # Transcription settings
    language: str | None = None  # None for auto-detect
    word_timestamps: bool = True

    # Diarization settings
    enable_diarization: bool = True
    hf_token: str | None = None
    num_speakers: int | None = None

    # Chunking settings (for large files)
    chunk_duration_sec: float = 30.0
    enable_chunking: bool = True
    chunk_threshold_sec: float = 300.0  # Enable chunking for files > 5 minutes


@dataclass
class TranscriptionOutput:
    """Output of the transcription engine."""

    text: str
    language: str
    duration: float
    segments: list[Segment] | list[SpeakerSegment]
    speakers: list[str] | None = None
    media_info: MediaInfo | None = None

    @property
    def has_diarization(self) -> bool:
        """Check if output has speaker diarization."""
        return self.speakers is not None and len(self.speakers) > 0

    def format_transcript(
        self,
        include_speakers: bool = True,
        include_timestamps: bool = False,
    ) -> str:
        """
        Format the transcript for output.

        :param include_speakers: Include speaker labels (if available).
        :param include_timestamps: Include timestamps.
        :returns: Formatted transcript string.
        """
        if self.has_diarization and include_speakers:
            return format_diarized_transcript(
                self.segments,  # type: ignore
                include_timestamps=include_timestamps,
            )

        # Simple format without speakers
        return format_simple_segments(
            self.segments,  # type: ignore
            include_timestamps=include_timestamps,
        )

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


class TranscriptionEngine:
    """
    Orchestrates the full transcription pipeline.

    Handles:
    - Input validation and format detection
    - Audio extraction from video
    - Memory-efficient chunking for large files
    - Whisper transcription
    - Speaker diarization (optional)
    - Progress reporting
    """

    def __init__(
        self,
        config: EngineConfig | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """
        Initialize the transcription engine.

        :param config: Engine configuration.
        :param progress_callback: Callback for progress updates.
                                  Called with (stage_name, progress_0_to_1).
        """
        self.config = config or EngineConfig()
        self.progress_callback = progress_callback
        self._transcriber: WhisperTranscriber | None = None
        self._diarizer: SpeakerDiarizer | None = None

    def _report_progress(self, stage: str, progress: float) -> None:
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(stage, min(1.0, max(0.0, progress)))

    def transcribe(self, input_path: str | Path) -> TranscriptionOutput:
        """
        Transcribe an audio or video file.

        :param input_path: Path to the input file.
        :returns: TranscriptionOutput with transcript and metadata.
        :raises FileNotFoundError: If input file doesn't exist.
        :raises UnsupportedFormatError: If format is not supported.
        :raises NoAudioStreamError: If file has no audio.
        :raises TranscriptionError: If transcription fails.
        """
        input_path = Path(input_path)

        # Stage 1: Validate input
        self._report_progress("Validating input", 0.0)
        media_info = validate_input_file(input_path)
        self._report_progress("Validating input", 1.0)

        # Stage 2: Prepare audio
        self._report_progress("Preparing audio", 0.0)
        prepared_path, is_temp = prepare_for_transcription(input_path)
        self._report_progress("Preparing audio", 1.0)

        try:
            # Stage 3: Transcribe
            self._report_progress("Transcribing", 0.0)

            # Decide whether to use chunking
            use_chunking = (
                self.config.enable_chunking
                and media_info.duration > self.config.chunk_threshold_sec
            )

            if use_chunking:
                result = self._transcribe_chunked(
                    prepared_path, media_info.duration
                )
            else:
                result = self._transcribe_full(prepared_path)

            self._report_progress("Transcribing", 1.0)

            # Stage 4: Diarization (optional)
            speakers = None
            final_segments: list[Segment] | list[SpeakerSegment] = (
                result.segments
            )

            if self.config.enable_diarization and self.config.hf_token:
                self._report_progress("Identifying speakers", 0.0)
                try:
                    diarized_segments = self._diarize(
                        prepared_path,
                        result.segments,
                        result.language,
                    )
                    final_segments = diarized_segments
                    speakers = list({s.speaker for s in diarized_segments})
                    speakers.sort()
                except Exception as e:
                    # Diarization failed, continue without it
                    logging.warning(f"Diarization failed: {e}")
                self._report_progress("Identifying speakers", 1.0)

            # Build output
            return TranscriptionOutput(
                text=result.text,
                language=result.language,
                duration=result.duration,
                segments=final_segments,
                speakers=speakers,
                media_info=media_info,
            )

        finally:
            # Clean up temp file
            if is_temp:
                cleanup_temp_file(prepared_path)

            # Clean up models to free memory
            self._cleanup()

    def _transcribe_full(self, audio_path: Path) -> TranscriptionResult:
        """Transcribe a file without chunking."""
        if self._transcriber is None:
            self._transcriber = WhisperTranscriber(
                model_size=self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )

        config = TranscriptionConfig(
            language=self.config.language,
            word_timestamps=self.config.word_timestamps,
        )

        return self._transcriber.transcribe(audio_path, config)

    def _transcribe_chunked(
        self,
        audio_path: Path,
        total_duration: float,
    ) -> TranscriptionResult:
        """Transcribe a large file in chunks."""
        if self._transcriber is None:
            self._transcriber = WhisperTranscriber(
                model_size=self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )

        config = TranscriptionConfig(
            language=self.config.language,
            word_timestamps=self.config.word_timestamps,
        )

        chunking_config = ChunkingConfig(
            chunk_duration_sec=self.config.chunk_duration_sec,
        )
        chunker = AudioChunker(config=chunking_config)

        chunk_results: list[tuple[AudioChunk, list[Segment]]] = []
        detected_language = None
        total_chunks = chunker.get_chunk_count(audio_path)

        try:
            for i, chunk in enumerate(chunker.chunk_audio(audio_path)):
                # Report progress
                progress = (i + 1) / total_chunks
                # Leave 10% for merging
                self._report_progress("Transcribing", progress * 0.9)
                # Transcribe chunk
                result = self._transcriber.transcribe(chunk.path, config)
                # Store first detected language
                if detected_language is None:
                    detected_language = result.language

                chunk_results.append((chunk, result.segments))

        finally:
            chunker.cleanup_all()

        # Merge results
        self._report_progress("Transcribing", 0.95)

        merged_segments = merge_chunk_segments(chunk_results)
        merged_text = merge_transcription_text(merged_segments)

        return TranscriptionResult(
            text=merged_text,
            language=detected_language or "unknown",
            language_probability=1.0,
            segments=merged_segments,
            duration=total_duration,
        )

    def _diarize(
        self,
        audio_path: Path,
        segments: list[Segment],
        language: str,
    ) -> list[SpeakerSegment]:
        """Run speaker diarization."""
        if self._diarizer is None:
            self._diarizer = SpeakerDiarizer(
                hf_token=self.config.hf_token,
                device=self.config.device,
            )

        return self._diarizer.diarize(
            audio_path,
            segments,
            language=language,
            num_speakers=self.config.num_speakers,
        )

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._transcriber is not None:
            self._transcriber.unload_model()
            self._transcriber = None

        if self._diarizer is not None:
            self._diarizer.unload_models()
            self._diarizer = None

        cleanup_gpu_memory()

    def __enter__(self) -> TranscriptionEngine:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self._cleanup()


def transcribe_file(  # noqa: PLR0913
    input_path: str | Path,
    *,
    model_size: ModelSize = "large-v3-turbo",
    language: str | None = None,
    enable_diarization: bool = False,
    hf_token: str | None = None,
    num_speakers: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> TranscriptionOutput:
    """
    Convenience function to transcribe a file.

    :param input_path: Path to input file.
    :param model_size: Whisper model size.
    :param language: Language code (None for auto-detect).
    :param enable_diarization: Enable speaker diarization.
    :param hf_token: HuggingFace token for diarization.
    :param num_speakers: Number of speakers (if known).
    :param progress_callback: Progress callback function.
    :returns: TranscriptionOutput with transcript.
    """
    config = EngineConfig(
        model_size=model_size,
        language=language,
        enable_diarization=enable_diarization,
        hf_token=hf_token,
        num_speakers=num_speakers,
    )

    with TranscriptionEngine(
        config=config, progress_callback=progress_callback
    ) as engine:
        return engine.transcribe(input_path)
