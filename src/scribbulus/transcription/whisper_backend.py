"""Whisper transcription backend using faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Literal

from scribbulus.utils.errors import ModelNotFoundError, TranscriptionError

# Model size options
ModelSize = Literal["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"]

# Device options
DeviceType = Literal["cuda", "cpu", "auto"]

# Compute type options
ComputeType = Literal["float16", "int8_float16", "int8", "float32"]


@dataclass
class Word:
    """A word with timing information."""

    word: str
    start: float
    end: float
    probability: float = 1.0


@dataclass
class Segment:
    """A transcription segment with timing information."""

    start: float
    end: float
    text: str
    words: list[Word] | None = None

    @property
    def duration(self) -> float:
        """Duration of this segment in seconds."""
        return self.end - self.start


@dataclass
class TranscriptionResult:
    """Result of transcription."""

    text: str
    language: str
    language_probability: float
    segments: list[Segment]
    duration: float

    @property
    def word_count(self) -> int:
        """Total word count in the transcription."""
        return len(self.text.split())


@dataclass
class TranscriptionConfig:
    """Configuration for transcription."""

    language: str | None = None  # None for auto-detect
    word_timestamps: bool = True
    beam_size: int = 5
    vad_filter: bool = True
    vad_min_silence_duration_ms: int = 500
    condition_on_previous_text: bool = True


class WhisperTranscriber:
    """
    Transcriber using faster-whisper.

    Provides a high-level interface for transcribing audio files
    using OpenAI's Whisper models optimized with CTranslate2.
    """

    def __init__(
        self,
        model_size: ModelSize = "large-v3-turbo",
        device: DeviceType = "auto",
        compute_type: ComputeType | None = None,
    ) -> None:
        """
        Initialize the transcriber.

        Args:
            model_size: Whisper model size.
            device: Device to use (cuda, cpu, or auto).
            compute_type: Compute type for inference. If None, auto-selected.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self) -> None:
        """Load the Whisper model lazily."""
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise ModelNotFoundError(
                self.model_size,
                "faster-whisper is not installed. Run: pip install faster-whisper",
            ) from e

        # Determine device
        device = self.device
        if device == "auto":
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        # Determine compute type
        compute_type = self.compute_type
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"

        try:
            self._model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
            )
        except Exception as e:
            raise ModelNotFoundError(self.model_size, str(e)) from e

    def transcribe(
        self,
        audio_path: str | Path,
        config: TranscriptionConfig | None = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file.
            config: Transcription configuration.

        Returns:
            TranscriptionResult with segments and metadata.

        Raises:
            TranscriptionError: If transcription fails.
            ModelNotFoundError: If the model cannot be loaded.
        """
        self._load_model()
        config = config or TranscriptionConfig()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        try:
            # Build transcription options
            vad_parameters = None
            if config.vad_filter:
                vad_parameters = {
                    "min_silence_duration_ms": config.vad_min_silence_duration_ms,
                }

            # Run transcription
            segments_iter, info = self._model.transcribe(
                str(audio_path),
                language=config.language,
                word_timestamps=config.word_timestamps,
                beam_size=config.beam_size,
                vad_filter=config.vad_filter,
                vad_parameters=vad_parameters,
                condition_on_previous_text=config.condition_on_previous_text,
            )

            # Convert segments to our format
            segments = []
            full_text_parts = []

            for segment in segments_iter:
                words = None
                if config.word_timestamps and hasattr(segment, "words") and segment.words:
                    words = [
                        Word(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            probability=word.probability if hasattr(word, "probability") else 1.0,
                        )
                        for word in segment.words
                    ]

                segments.append(
                    Segment(
                        start=segment.start,
                        end=segment.end,
                        text=segment.text,
                        words=words,
                    )
                )
                full_text_parts.append(segment.text.strip())

            # Calculate duration from last segment
            duration = segments[-1].end if segments else 0.0

            return TranscriptionResult(
                text=" ".join(full_text_parts),
                language=info.language,
                language_probability=info.language_probability,
                segments=segments,
                duration=duration,
            )

        except Exception as e:
            if "CUDA" in str(e) or "cuda" in str(e):
                raise TranscriptionError(
                    f"CUDA error: {e}. Try using --device cpu or check CUDA installation."
                ) from e
            raise TranscriptionError(str(e)) from e

    def transcribe_streaming(
        self,
        audio_path: str | Path,
        config: TranscriptionConfig | None = None,
    ) -> Iterator[Segment]:
        """
        Transcribe an audio file, yielding segments as they're processed.

        This is more memory-efficient for long files as segments are
        yielded one at a time.

        Args:
            audio_path: Path to the audio file.
            config: Transcription configuration.

        Yields:
            Segment instances as they're transcribed.

        Raises:
            TranscriptionError: If transcription fails.
        """
        self._load_model()
        config = config or TranscriptionConfig()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        try:
            vad_parameters = None
            if config.vad_filter:
                vad_parameters = {
                    "min_silence_duration_ms": config.vad_min_silence_duration_ms,
                }

            segments_iter, info = self._model.transcribe(
                str(audio_path),
                language=config.language,
                word_timestamps=config.word_timestamps,
                beam_size=config.beam_size,
                vad_filter=config.vad_filter,
                vad_parameters=vad_parameters,
                condition_on_previous_text=config.condition_on_previous_text,
            )

            for segment in segments_iter:
                words = None
                if config.word_timestamps and hasattr(segment, "words") and segment.words:
                    words = [
                        Word(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            probability=word.probability if hasattr(word, "probability") else 1.0,
                        )
                        for word in segment.words
                    ]

                yield Segment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    words=words,
                )

        except Exception as e:
            raise TranscriptionError(str(e)) from e

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self._model is not None:
            del self._model
            self._model = None

            # Try to free GPU memory
            try:
                import gc

                import torch

                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

    def __enter__(self) -> "WhisperTranscriber":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - unload model."""
        self.unload_model()


def detect_language(
    audio_path: str | Path,
    model_size: ModelSize = "base",
) -> tuple[str, float]:
    """
    Detect the language of an audio file.

    Uses a smaller model by default for faster detection.

    Args:
        audio_path: Path to the audio file.
        model_size: Model size to use for detection.

    Returns:
        Tuple of (language_code, probability).
    """
    with WhisperTranscriber(model_size=model_size) as transcriber:
        transcriber._load_model()

        try:
            from faster_whisper import WhisperModel

            # Load audio and detect language
            audio = transcriber._model.feature_extractor(str(audio_path))
            # Pad or trim to 30 seconds
            if len(audio) > 480000:  # 30 seconds at 16kHz
                audio = audio[:480000]

            # Detect language
            _, probs = transcriber._model.model.detect_language(audio)
            detected_lang = max(probs, key=probs.get)
            return detected_lang, probs[detected_lang]

        except Exception as e:
            raise TranscriptionError(f"Language detection failed: {e}") from e
