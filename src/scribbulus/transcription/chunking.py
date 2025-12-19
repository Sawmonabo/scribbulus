"""Memory-efficient audio chunking for large file transcription."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from scribbulus.media.audio_prep import cleanup_temp_file, extract_audio_chunk
from scribbulus.media.ffmpeg import get_audio_duration
from scribbulus.transcription.whisper_backend import Segment


@dataclass
class AudioChunk:
    """Represents a chunk of audio for processing."""

    path: Path
    start_time: float  # Global start time in source audio
    end_time: float  # Global end time in source audio
    index: int  # Chunk index
    is_last: bool  # Flag for final chunk

    @property
    def duration(self) -> float:
        """Duration of this chunk in seconds."""
        return self.end_time - self.start_time


@dataclass
class ChunkingConfig:
    """Configuration for audio chunking."""

    chunk_duration_sec: float = 30.0  # Duration of each chunk
    overlap_sec: float = 1.0  # Overlap between chunks for context
    sample_rate: int = 16000  # Target sample rate
    mono: bool = True  # Convert to mono

    def __post_init__(self) -> None:
        if self.chunk_duration_sec <= 0:
            raise ValueError("chunk_duration_sec must be positive")
        if self.overlap_sec < 0:
            raise ValueError("overlap_sec cannot be negative")
        if self.overlap_sec >= self.chunk_duration_sec:
            raise ValueError(
                "overlap_sec must be less than chunk_duration_sec"
            )


class AudioChunker:
    """
    Process large audio files in memory-efficient chunks.

    Never loads the full audio into RAM. Uses ffmpeg to extract
    segments on-demand with fast seeking.
    """

    def __init__(
        self,
        config: ChunkingConfig | None = None,
        temp_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize the chunker.

        :param config: Chunking configuration.
        :param temp_dir: Directory for temporary chunk files.
        """
        self.config = config or ChunkingConfig()
        self.temp_dir = (
            Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        )
        self._active_chunks: list[Path] = []

    def chunk_audio(self, audio_path: str | Path) -> Iterator[AudioChunk]:
        """
        Yield audio chunks without loading full file.

        Uses ffmpeg to extract segments on-demand with fast seeking.
        Chunks are automatically cleaned up after yielding.

        :param audio_path: Path to the audio file.
        :returns: AudioChunk instances for processing.
        """
        audio_path = Path(audio_path)
        duration = get_audio_duration(audio_path)

        chunk_duration = self.config.chunk_duration_sec
        overlap = self.config.overlap_sec
        step = chunk_duration - overlap

        start = 0.0
        index = 0
        previous_chunk: Path | None = None

        while start < duration:
            # Calculate chunk boundaries
            end = min(start + chunk_duration, duration)
            actual_duration = end - start
            is_last = end >= duration

            # Generate chunk file path
            chunk_path = self._get_chunk_path(audio_path, index)

            # Extract chunk
            extract_audio_chunk(
                audio_path,
                chunk_path,
                start_time=start,
                duration=actual_duration,
                sample_rate=self.config.sample_rate,
                mono=self.config.mono,
            )

            self._active_chunks.append(chunk_path)

            # Clean up previous chunk (after it's been processed)
            if previous_chunk is not None:
                self._cleanup_chunk(previous_chunk)

            yield AudioChunk(
                path=chunk_path,
                start_time=start,
                end_time=end,
                index=index,
                is_last=is_last,
            )

            previous_chunk = chunk_path

            # Move to next chunk
            start += step
            index += 1

        # Clean up last chunk
        if previous_chunk is not None:
            self._cleanup_chunk(previous_chunk)

    def _get_chunk_path(self, source_path: Path, index: int) -> Path:
        """Generate a unique path for a chunk file."""
        chunk_name = f"chunk_{source_path.stem}_{os.getpid()}_{index}.wav"
        return self.temp_dir / chunk_name

    def _cleanup_chunk(self, chunk_path: Path) -> None:
        """Clean up a chunk file."""
        cleanup_temp_file(chunk_path)
        if chunk_path in self._active_chunks:
            self._active_chunks.remove(chunk_path)

    def cleanup_all(self) -> None:
        """Clean up all active chunk files."""
        for chunk_path in list(self._active_chunks):
            self._cleanup_chunk(chunk_path)

    def get_chunk_count(self, audio_path: str | Path) -> int:
        """
        Calculate the number of chunks for an audio file.

        :param audio_path: Path to the audio file.
        :returns: Number of chunks that will be generated.
        """
        duration = get_audio_duration(audio_path)
        chunk_duration = self.config.chunk_duration_sec
        overlap = self.config.overlap_sec
        step = chunk_duration - overlap

        # Calculate number of chunks
        if duration <= chunk_duration:
            return 1

        # First chunk covers chunk_duration,
        # subsequent chunks step by (chunk_duration - overlap)
        remaining = duration - chunk_duration
        additional_chunks = int(remaining / step)
        if remaining % step > 0:
            additional_chunks += 1

        return 1 + additional_chunks


def merge_chunk_segments(
    chunk_segments: list[tuple[AudioChunk, list[Segment]]],
    overlap_threshold: float = 0.5,
) -> list[Segment]:
    """
    Merge transcription segments from multiple chunks.

    Handles overlap regions by deduplicating based on timestamps.

    :param chunk_segments: List of (AudioChunk, segments) tuples.
    :param overlap_threshold: Threshold for considering segments as duplicates.
    :returns: Merged list of segments with adjusted timestamps.
    """
    if not chunk_segments:
        return []

    merged_segments: list[Segment] = []

    for chunk, segments in chunk_segments:
        for segment in segments:
            # Adjust timestamps to global time
            adjusted_start = segment.start + chunk.start_time
            adjusted_end = segment.end + chunk.start_time

            # Check for overlap with existing segments
            is_duplicate = False
            for existing in merged_segments:
                # Check if this segment overlaps significantly w/existing one
                overlap_start = max(adjusted_start, existing.start)
                overlap_end = min(adjusted_end, existing.end)
                overlap_duration = max(0, overlap_end - overlap_start)

                segment_duration = adjusted_end - adjusted_start
                if (
                    segment_duration > 0
                    and overlap_duration / segment_duration > overlap_threshold
                ):
                    is_duplicate = True
                    break

            if not is_duplicate:
                # Create new segment with adjusted timestamps
                adjusted_segment = Segment(
                    start=adjusted_start,
                    end=adjusted_end,
                    text=segment.text,
                    words=segment.words,
                )
                merged_segments.append(adjusted_segment)

    # Sort by start time
    merged_segments.sort(key=lambda s: s.start)

    return merged_segments


def merge_transcription_text(segments: list[Segment]) -> str:
    """
    Merge segment texts into a single transcript.

    :param segments: List of segments.
    :returns: Merged transcript text.
    """
    texts = [
        segment.text.strip() for segment in segments if segment.text.strip()
    ]
    return " ".join(texts)
