"""Centralized type definitions for scribbulus.

This module contains reusable type aliases that are shared across
multiple modules. Domain-specific types that are only used within
a single module should remain in that module.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, Literal, Protocol, runtime_checkable

# Device types for compute operations
DeviceType = Literal["cuda", "cpu", "auto"]
"""User-facing device selection including auto-detection."""

ResolvedDeviceType = Literal["cuda", "cpu"]
"""Resolved device type after auto-detection (no 'auto')."""

ModelSize = Literal[
    "tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"
]
"""Available Whisper model sizes."""

ComputeType = Literal["float16", "int8_float16", "int8", "float32"]
"""Compute precision types for inference."""

ProgressCallback = Callable[[str, float], None]
"""Callback function for progress updates."""

# =============================================================================
# Protocol classes for external library type hints
# =============================================================================
# These protocols define the interfaces we use from faster-whisper and whisperx,
# enabling IDE autocomplete and type checking without requiring the libraries
# to be installed.


@runtime_checkable
class WordProtocol(Protocol):
    """Protocol for faster-whisper Word objects."""

    word: str
    start: float
    end: float
    probability: float


@runtime_checkable
class SegmentProtocol(Protocol):
    """Protocol for faster-whisper Segment objects."""

    start: float
    end: float
    text: str
    words: list[WordProtocol] | None


@runtime_checkable
class TranscriptionInfoProtocol(Protocol):
    """Protocol for faster-whisper TranscriptionInfo objects."""

    language: str
    language_probability: float
    duration: float


class FeatureExtractorProtocol(Protocol):
    """Protocol for faster-whisper FeatureExtractor."""

    def __call__(
        self,
        waveform: str,
        padding: int = 160,
        chunk_length: int | None = None,
    ) -> Any: ...


class WhisperModelInnerProtocol(Protocol):
    """Protocol for the inner model used for language detection."""

    def detect_language(self, audio: Any) -> tuple[Any, dict[str, float]]: ...


class WhisperModelProtocol(Protocol):
    """Protocol for faster-whisper WhisperModel instances."""

    feature_extractor: FeatureExtractorProtocol
    model: WhisperModelInnerProtocol

    def __init__(
        self,
        model_size_or_path: str,
        device: DeviceType | ResolvedDeviceType = "auto",
        compute_type: ComputeType | str | None = "default",
        **kwargs: Any,
    ) -> None: ...

    def transcribe(  # noqa: PLR0913 - matches external API
        self,
        audio: str,
        *,
        language: str | None = None,
        word_timestamps: bool = True,
        beam_size: int = 5,
        vad_filter: bool = True,
        vad_parameters: dict[str, Any] | None = None,
        condition_on_previous_text: bool = True,
    ) -> tuple[Iterator[SegmentProtocol], TranscriptionInfoProtocol]: ...


# whisperx Protocols


class DiarizationPipelineProtocol(Protocol):
    """Protocol for whisperx DiarizationPipeline."""

    def __call__(
        self,
        audio: Any,
        *,
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> dict[str, Any]: ...


class WhisperXModuleProtocol(Protocol):
    """Protocol for whisperx module interface."""

    def DiarizationPipeline(  # noqa: N802 - matches external API
        self,
        use_auth_token: str | None = None,
        device: str = "cpu",
    ) -> DiarizationPipelineProtocol: ...

    def load_audio(self, audio_path: str) -> Any: ...

    def load_align_model(
        self,
        language_code: str,
        device: str,
    ) -> tuple[Any, Any]: ...

    def align(  # noqa: PLR0913 - matches external API
        self,
        segments: list[dict[str, Any]],
        model: Any,
        metadata: Any,
        audio: Any,
        device: str,
        return_char_alignments: bool = False,
    ) -> dict[str, Any]: ...

    def assign_word_speakers(
        self,
        diarize_segments: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]: ...
