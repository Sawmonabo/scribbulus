"""Tests for audio chunking module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scribbulus.transcription.chunking import (
    AudioChunk,
    AudioChunker,
    ChunkingConfig,
    merge_chunk_segments,
    merge_transcription_text,
)


class TestChunkingConfig:
    """Test ChunkingConfig dataclass."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = ChunkingConfig()

        assert config.chunk_duration_sec == 30.0
        assert config.overlap_sec == 1.0
        assert config.temp_dir is None

    def test_custom_values(self):
        """Should accept custom values."""
        config = ChunkingConfig(
            chunk_duration_sec=60.0,
            overlap_sec=2.0,
            temp_dir=Path("/tmp/chunks"),
        )

        assert config.chunk_duration_sec == 60.0
        assert config.overlap_sec == 2.0
        assert config.temp_dir == Path("/tmp/chunks")


class TestAudioChunk:
    """Test AudioChunk dataclass."""

    def test_chunk_creation(self, temp_dir):
        """Should create chunk with all properties."""
        chunk_path = temp_dir / "chunk_0.wav"
        chunk_path.write_bytes(b"fake audio")

        chunk = AudioChunk(
            path=chunk_path,
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            index=0,
        )

        assert chunk.path == chunk_path
        assert chunk.start_time == 0.0
        assert chunk.end_time == 30.0
        assert chunk.duration == 30.0
        assert chunk.index == 0


class TestAudioChunker:
    """Test AudioChunker class."""

    def test_chunker_initialization(self):
        """Should initialize with default config."""
        chunker = AudioChunker()

        assert chunker.config is not None
        assert chunker.config.chunk_duration_sec == 30.0

    def test_chunker_with_custom_config(self):
        """Should accept custom configuration."""
        config = ChunkingConfig(chunk_duration_sec=60.0)
        chunker = AudioChunker(config=config)

        assert chunker.config.chunk_duration_sec == 60.0

    def test_get_chunk_count(self):
        """Should calculate correct number of chunks."""
        chunker = AudioChunker(
            config=ChunkingConfig(
                chunk_duration_sec=30.0,
                overlap_sec=1.0,
            )
        )

        with patch.object(chunker, "_get_audio_duration", return_value=90.0):
            count = chunker.get_chunk_count(Path("test.wav"))

        # 90 seconds with 30s chunks and 1s overlap
        # Chunk 0: 0-30, Chunk 1: 29-59, Chunk 2: 58-88, Chunk 3: 87-90
        assert count >= 3

    def test_get_chunk_count_short_audio(self):
        """Should return 1 for audio shorter than chunk duration."""
        chunker = AudioChunker(
            config=ChunkingConfig(chunk_duration_sec=30.0)
        )

        with patch.object(chunker, "_get_audio_duration", return_value=10.0):
            count = chunker.get_chunk_count(Path("test.wav"))

        assert count == 1

    def test_chunk_audio_yields_chunks(self, temp_dir):
        """chunk_audio should yield AudioChunk objects."""
        chunker = AudioChunker(
            config=ChunkingConfig(
                chunk_duration_sec=30.0,
                temp_dir=temp_dir,
            )
        )

        # Create a fake source audio file
        source_file = temp_dir / "source.wav"
        source_file.write_bytes(b"fake audio data")

        with patch.object(chunker, "_get_audio_duration", return_value=60.0):
            with patch(
                "scribbulus.transcription.chunking.extract_audio_chunk"
            ) as mock_extract:
                # Mock extract to create fake chunk files
                def create_chunk(input_path, output_path, **kwargs):
                    output_path.write_bytes(b"chunk data")
                    return output_path

                mock_extract.side_effect = create_chunk

                chunks = list(chunker.chunk_audio(source_file))

        assert len(chunks) >= 2
        assert all(isinstance(c, AudioChunk) for c in chunks)

    def test_cleanup_all(self, temp_dir):
        """cleanup_all should remove all temporary chunk files."""
        chunker = AudioChunker(
            config=ChunkingConfig(temp_dir=temp_dir)
        )

        # Manually add some paths to track
        chunk1 = temp_dir / "chunk_0.wav"
        chunk2 = temp_dir / "chunk_1.wav"
        chunk1.write_bytes(b"chunk 1")
        chunk2.write_bytes(b"chunk 2")

        chunker._temp_chunks = [chunk1, chunk2]

        chunker.cleanup_all()

        assert not chunk1.exists()
        assert not chunk2.exists()


class TestMergeChunkSegments:
    """Test segment merging functions."""

    def test_merge_empty_results(self):
        """Should handle empty results."""
        result = merge_chunk_segments([])
        assert result == []

    def test_merge_single_chunk(self):
        """Should handle single chunk without modification."""
        segment = MagicMock()
        segment.start = 0.0
        segment.end = 5.0
        segment.text = "Hello world"

        chunk = AudioChunk(
            path=Path("chunk.wav"),
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            index=0,
        )

        result = merge_chunk_segments([(chunk, [segment])])

        assert len(result) == 1
        assert result[0].text == "Hello world"

    def test_merge_adjusts_timestamps(self):
        """Should adjust segment timestamps based on chunk offset."""
        segment = MagicMock()
        segment.start = 5.0  # Local time within chunk
        segment.end = 10.0
        segment.text = "Test"

        chunk = AudioChunk(
            path=Path("chunk.wav"),
            start_time=30.0,  # Chunk starts at 30s in original
            end_time=60.0,
            duration=30.0,
            index=1,
        )

        result = merge_chunk_segments([(chunk, [segment])])

        # Timestamps should be adjusted: 5+30=35, 10+30=40
        assert result[0].start == 35.0
        assert result[0].end == 40.0

    def test_merge_removes_duplicates_in_overlap(self):
        """Should handle overlapping regions between chunks."""
        # Segment from chunk 1
        seg1 = MagicMock()
        seg1.start = 28.0
        seg1.end = 30.0
        seg1.text = "overlap text"

        chunk1 = AudioChunk(
            path=Path("chunk1.wav"),
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            index=0,
        )

        # Similar segment from chunk 2 (in overlap region)
        seg2 = MagicMock()
        seg2.start = 0.0  # Local time in chunk 2
        seg2.end = 2.0
        seg2.text = "overlap text"

        chunk2 = AudioChunk(
            path=Path("chunk2.wav"),
            start_time=29.0,  # Starts 1s before chunk1 ends
            end_time=59.0,
            duration=30.0,
            index=1,
        )

        # New segment in chunk 2
        seg3 = MagicMock()
        seg3.start = 5.0
        seg3.end = 10.0
        seg3.text = "new text"

        result = merge_chunk_segments([
            (chunk1, [seg1]),
            (chunk2, [seg2, seg3]),
        ])

        # Should have filtered duplicate
        texts = [s.text for s in result]
        assert texts.count("overlap text") == 1


class TestMergeTranscriptionText:
    """Test text merging function."""

    def test_merge_empty_segments(self):
        """Should handle empty segment list."""
        result = merge_transcription_text([])
        assert result == ""

    def test_merge_single_segment(self):
        """Should return text from single segment."""
        segment = MagicMock()
        segment.text = "Hello world"

        result = merge_transcription_text([segment])
        assert result == "Hello world"

    def test_merge_multiple_segments(self):
        """Should join multiple segments with space."""
        seg1 = MagicMock()
        seg1.text = "Hello"

        seg2 = MagicMock()
        seg2.text = "world"

        result = merge_transcription_text([seg1, seg2])
        assert result == "Hello world"

    def test_merge_strips_whitespace(self):
        """Should strip extra whitespace."""
        seg1 = MagicMock()
        seg1.text = "  Hello  "

        seg2 = MagicMock()
        seg2.text = "  world  "

        result = merge_transcription_text([seg1, seg2])
        assert result == "Hello world"
