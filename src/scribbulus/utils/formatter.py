"""Text formatting utilities for transcript output.

This module provides functions for formatting transcription text with
proper line wrapping, speaker labels, and timestamps while preserving
semantic structure.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scribbulus.transcription.diarization import SpeakerSegment
    from scribbulus.transcription.whisper_backend import Segment


# Default line width for text wrapping
DEFAULT_LINE_WIDTH = 80


@dataclass
class FormatterConfig:
    """Configuration for transcript formatting."""

    line_width: int = DEFAULT_LINE_WIDTH
    blank_line_between_speakers: bool = True


def wrap_text(
    text: str,
    width: int = DEFAULT_LINE_WIDTH,
    initial_indent: str = "",
    subsequent_indent: str = "",
) -> str:
    """
    Wrap text to specified width, handling edge cases.

    Uses textwrap.fill() but handles edge cases like:
    - Very long words (>width) are preserved intact
    - Empty strings return empty strings
    - Preserves existing paragraph breaks

    :param text: The text to wrap.
    :param width: Maximum line width.
    :param initial_indent: Indent for first line.
    :param subsequent_indent: Indent for continuation lines.
    :returns: Wrapped text string.
    """
    if not text or not text.strip():
        return ""

    # Handle edge case: if width is too small, use minimum
    effective_width = max(width, 20)

    return textwrap.fill(
        text,
        width=effective_width,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=True,
    )


def format_time(seconds: float) -> str:
    """
    Format seconds as MM:SS or HH:MM:SS.

    :param seconds: Time in seconds.
    :returns: Formatted time string.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _build_speaker_block(
    speaker: str,
    texts: list[str],
    start_time: float,
    include_timestamps: bool,
    config: FormatterConfig,
) -> str:
    """
    Build a formatted block for a single speaker's content.

    :param speaker: Speaker identifier.
    :param texts: List of text segments for this speaker.
    :param start_time: Start time of this speaker block.
    :param include_timestamps: Include timestamp in header.
    :param config: Formatting configuration.
    :returns: Formatted speaker block.
    """
    # Build header line
    if include_timestamps:
        header = f"[{speaker}] ({format_time(start_time)})"
    else:
        header = f"[{speaker}]"

    # Join all texts for this speaker
    combined_text = " ".join(texts)

    # Wrap the text
    wrapped = wrap_text(combined_text, width=config.line_width)

    return f"{header}\n{wrapped}"


def format_diarized_segments(
    segments: list[SpeakerSegment],
    include_timestamps: bool = False,
    config: FormatterConfig | None = None,
) -> str:
    """
    Format diarized segments into a readable transcript.

    Groups consecutive segments by speaker, joining text on the same
    line until speaker changes. Wraps text at specified line width.

    :param segments: List of speaker segments.
    :param include_timestamps: Include timestamps in output.
    :param config: Formatting configuration.
    :returns: Formatted transcript string.
    """
    if not segments:
        return ""

    config = config or FormatterConfig()
    output_blocks: list[str] = []

    current_speaker: str | None = None
    current_texts: list[str] = []
    current_start_time: float = 0.0

    for segment in segments:
        if segment.speaker != current_speaker:
            # Flush previous speaker's content
            if current_speaker is not None and current_texts:
                block = _build_speaker_block(
                    speaker=current_speaker,
                    texts=current_texts,
                    start_time=current_start_time,
                    include_timestamps=include_timestamps,
                    config=config,
                )
                output_blocks.append(block)

            # Start new speaker
            current_speaker = segment.speaker
            current_texts = []
            current_start_time = segment.start

        # Accumulate text for current speaker
        text = segment.text.strip()
        if text:
            current_texts.append(text)

    # Flush final speaker's content
    if current_speaker is not None and current_texts:
        block = _build_speaker_block(
            speaker=current_speaker,
            texts=current_texts,
            start_time=current_start_time,
            include_timestamps=include_timestamps,
            config=config,
        )
        output_blocks.append(block)

    separator = "\n\n" if config.blank_line_between_speakers else "\n"
    return separator.join(output_blocks)


def format_simple_segments(
    segments: list[Segment],
    include_timestamps: bool = False,
    config: FormatterConfig | None = None,
) -> str:
    """
    Format segments without speaker diarization.

    :param segments: List of transcription segments.
    :param include_timestamps: Include timestamps in output.
    :param config: Formatting configuration.
    :returns: Formatted transcript string.
    """
    if not segments:
        return ""

    config = config or FormatterConfig()

    if include_timestamps:
        # With timestamps: each segment gets its own line with timestamp
        lines = []
        for segment in segments:
            time_str = format_time(segment.start)
            text = segment.text.strip()
            if text:
                # Calculate available width after timestamp prefix
                prefix = f"[{time_str}] "
                available_width = config.line_width - len(prefix)
                wrapped = wrap_text(text, width=available_width)
                # Indent continuation lines to align with first line
                indented = wrapped.replace("\n", "\n" + " " * len(prefix))
                lines.append(f"{prefix}{indented}")
        return "\n".join(lines)

    # Without timestamps: combine all text and wrap
    combined = " ".join(
        seg.text.strip() for seg in segments if seg.text.strip()
    )
    return wrap_text(combined, width=config.line_width)


__all__ = [
    "DEFAULT_LINE_WIDTH",
    "FormatterConfig",
    "format_diarized_segments",
    "format_simple_segments",
    "format_time",
    "wrap_text",
]
