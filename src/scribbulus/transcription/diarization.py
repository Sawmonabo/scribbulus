"""Speaker diarization using WhisperX and pyannote."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

from scribbulus.utils.deps import (
    cleanup_gpu_memory,
    get_device,
    get_diarization_pipeline,
    get_whisperx,
)
from scribbulus.utils.errors import DiarizationError, HuggingFaceTokenError
from scribbulus.utils.formatter import format_diarized_segments
from scribbulus.utils.types import (
    DeviceType,
    DiarizationPipelineProtocol,
    ResolvedDeviceType,
)

if TYPE_CHECKING:
    from scribbulus.transcription.whisper_backend import Segment


@dataclass
class SpeakerSegment:
    """A segment with speaker identification."""

    start: float
    end: float
    text: str
    speaker: str
    words: list[Any] | None = None

    @property
    def duration(self) -> float:
        """Duration of this segment in seconds."""
        return self.end - self.start


@dataclass
class DiarizedResult:
    """Result of transcription with speaker diarization."""

    text: str
    language: str
    segments: list[SpeakerSegment]
    speakers: list[str]
    duration: float

    @property
    def speaker_count(self) -> int:
        """Number of unique speakers."""
        return len(self.speakers)

    def get_speaker_segments(self, speaker: str) -> list[SpeakerSegment]:
        """Get all segments for a specific speaker."""
        return [s for s in self.segments if s.speaker == speaker]


class SpeakerDiarizer:
    """
    Speaker diarization using WhisperX and pyannote.

    Identifies "who spoke when" in an audio recording.
    Requires a HuggingFace token with access to pyannote models.
    """

    def __init__(
        self,
        hf_token: str | None = None,
        device: DeviceType = "auto",
    ) -> None:
        """
        Initialize the diarizer.

        :param hf_token: HuggingFace token for pyannote models.
                         Falls back to HF_TOKEN environment variable.
        :param device: Device to use (cuda, cpu, or auto).
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.device = device
        self._diarize_model: DiarizationPipelineProtocol | None = None
        self._align_model = None

    def _get_device(self) -> ResolvedDeviceType:
        """Get the actual device to use."""
        return get_device(self.device)

    def _load_diarize_model(self) -> None:
        """Load the diarization pipeline lazily."""
        if self._diarize_model is not None:
            return

        if not self.hf_token:
            raise HuggingFaceTokenError()

        # Get DiarizationPipeline class from whisperx.diarize submodule
        # (raises DiarizationError if whisperx not installed)
        DiarizationPipeline = get_diarization_pipeline()  # noqa: N806

        try:
            device = self._get_device()
            self._diarize_model = DiarizationPipeline(
                use_auth_token=self.hf_token,
                device=device,
            )
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                raise DiarizationError(
                    "Invalid HuggingFace token or model access denied. "
                    "Make sure you've accepted the model terms at "
                    "https://huggingface.co/pyannote/speaker-diarization-3.1"
                ) from e
            raise DiarizationError(
                f"Failed to load diarization model: {e}"
            ) from e

    def diarize(  # noqa: PLR0913 - diarization requires multiple speaker params
        self,
        audio_path: str | Path,
        transcription_segments: list[Segment],
        language: str = "en",
        num_speakers: int | None = None,
        min_speakers: int | None = None,
        max_speakers: int | None = None,
    ) -> list[SpeakerSegment]:
        """
        Add speaker labels to transcription segments.

        :param audio_path: Path to the audio file.
        :param transcription_segments: Segments from transcription.
        :param language: Language code for alignment.
        :param num_speakers: Exact number of speakers (if known).
        :param min_speakers: Minimum number of speakers.
        :param max_speakers: Maximum number of speakers.
        :returns: List of SpeakerSegment with speaker labels.
        :raises DiarizationError: If diarization fails.
        :raises HuggingFaceTokenError: If HF token is missing.
        """
        self._load_diarize_model()
        assert self._diarize_model is not None

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise DiarizationError(f"Audio file not found: {audio_path}")

        whisperx = get_whisperx()
        device = self._get_device()

        try:
            audio = whisperx.load_audio(str(audio_path))

            # Convert segments to whisperx format
            segments_dict = [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                }
                for seg in transcription_segments
            ]

            # Load alignment model and align
            model_a, metadata = whisperx.load_align_model(
                language_code=language,
                device=device,
            )

            result = whisperx.align(
                segments_dict,
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False,
            )

            # Unload alignment model to free memory
            del model_a

            # Run diarization
            diarize_kwargs = {}
            if num_speakers is not None:
                diarize_kwargs["num_speakers"] = num_speakers
            if min_speakers is not None:
                diarize_kwargs["min_speakers"] = min_speakers
            if max_speakers is not None:
                diarize_kwargs["max_speakers"] = max_speakers

            diarize_segments = self._diarize_model(audio, **diarize_kwargs)

            # Assign speakers to words/segments
            result = whisperx.assign_word_speakers(diarize_segments, result)

            # Convert to our format
            speaker_segments = []
            for segment in result.get("segments", []):
                speaker = segment.get("speaker", "UNKNOWN")
                speaker_segments.append(
                    SpeakerSegment(
                        start=segment["start"],
                        end=segment["end"],
                        text=segment["text"],
                        speaker=speaker,
                        words=segment.get("words"),
                    )
                )

            return speaker_segments

        except Exception as e:
            if "CUDA" in str(e) or "cuda" in str(e):
                raise DiarizationError(
                    f"CUDA error during diarization: {e}. "
                    "Try without diarization or check CUDA installation."
                ) from e
            raise DiarizationError(str(e)) from e

    def unload_models(self) -> None:
        """Unload models to free memory."""
        if self._diarize_model is not None:
            del self._diarize_model
            self._diarize_model = None

        if self._align_model is not None:
            del self._align_model
            self._align_model = None

        cleanup_gpu_memory()

    def __enter__(self) -> SpeakerDiarizer:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit - unload models."""
        self.unload_models()


def format_diarized_transcript(
    segments: list[SpeakerSegment],
    include_timestamps: bool = False,
) -> str:
    """
    Format diarized segments into a readable transcript.

    :param segments: List of speaker segments.
    :param include_timestamps: Include timestamps in output.
    :returns: Formatted transcript string.
    """
    return format_diarized_segments(
        segments,
        include_timestamps=include_timestamps,
    )


def _format_time(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def get_speaker_stats(
    segments: list[SpeakerSegment],
) -> dict[str, dict[str, Any]]:
    """
    Get statistics for each speaker.

    :param segments: List of speaker segments.
    :returns: Dictionary with speaker stats (duration, word count, etc.).
    """
    stats: dict[str, dict[str, Any]] = {}

    for segment in segments:
        speaker = segment.speaker
        if speaker not in stats:
            stats[speaker] = {
                "duration": 0.0,
                "segment_count": 0,
                "word_count": 0,
            }

        stats[speaker]["duration"] += segment.duration
        stats[speaker]["segment_count"] += 1
        stats[speaker]["word_count"] += len(segment.text.split())

    return stats
