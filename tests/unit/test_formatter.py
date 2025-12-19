"""Tests for text formatting utilities."""

from __future__ import annotations

from dataclasses import dataclass

from scribbulus.utils.formatter import (
    DEFAULT_LINE_WIDTH,
    FormatterConfig,
    format_diarized_segments,
    format_simple_segments,
    format_time,
    wrap_text,
)


# Mock segment classes for testing
@dataclass
class MockSegment:
    """Mock segment for testing format_simple_segments."""

    start: float
    end: float
    text: str


@dataclass
class MockSpeakerSegment:
    """Mock speaker segment for testing format_diarized_segments."""

    start: float
    end: float
    text: str
    speaker: str


class TestWrapText:
    """Tests for wrap_text function."""

    def test_wraps_at_default_width(self):
        """Text should wrap at 80 characters by default."""
        long_text = "word " * 30  # ~150 chars
        result = wrap_text(long_text)
        lines = result.split("\n")
        assert all(len(line) <= DEFAULT_LINE_WIDTH for line in lines)

    def test_preserves_long_words(self):
        """Long words should not be broken."""
        url = "https://example.com/very/long/path/to/resource/that/exceeds"
        result = wrap_text(f"Check this out: {url}")
        assert url in result

    def test_empty_string_returns_empty(self):
        """Empty input should return empty string."""
        assert wrap_text("") == ""
        assert wrap_text("   ") == ""

    def test_whitespace_only_returns_empty(self):
        """Whitespace-only input should return empty string."""
        assert wrap_text("\n\n\n") == ""
        assert wrap_text("\t\t") == ""

    def test_respects_custom_width(self):
        """Should respect custom line width."""
        text = "word " * 20
        result = wrap_text(text, width=40)
        lines = result.split("\n")
        assert all(len(line) <= 40 for line in lines)

    def test_minimum_width_enforced(self):
        """Very small widths should use minimum of 20."""
        text = "This is a test sentence that needs wrapping."
        result = wrap_text(text, width=5)
        # Should not crash and should produce output
        assert result
        # Lines should be no longer than minimum width (20)
        lines = result.split("\n")
        assert all(len(line) <= 20 for line in lines)

    def test_initial_indent(self):
        """Should respect initial indent."""
        text = "This is a test."
        result = wrap_text(text, initial_indent=">>> ")
        assert result.startswith(">>> ")

    def test_subsequent_indent(self):
        """Should respect subsequent indent."""
        text = "word " * 30  # Long enough to wrap
        result = wrap_text(text, width=40, subsequent_indent="    ")
        lines = result.split("\n")
        if len(lines) > 1:
            assert lines[1].startswith("    ")


class TestFormatTime:
    """Tests for format_time function."""

    def test_formats_seconds_only(self):
        """Should format seconds less than a minute."""
        assert format_time(0) == "00:00"
        assert format_time(30) == "00:30"
        assert format_time(59) == "00:59"

    def test_formats_minutes_and_seconds(self):
        """Should format minutes and seconds."""
        assert format_time(60) == "01:00"
        assert format_time(65) == "01:05"
        assert format_time(125) == "02:05"
        assert format_time(3599) == "59:59"

    def test_formats_hours(self):
        """Should format hours when >= 1 hour."""
        assert format_time(3600) == "01:00:00"
        assert format_time(3661) == "01:01:01"
        assert format_time(7200) == "02:00:00"
        assert format_time(36000) == "10:00:00"

    def test_handles_float_input(self):
        """Should handle float seconds."""
        assert format_time(65.7) == "01:05"
        assert format_time(65.999) == "01:05"

    def test_handles_large_values(self):
        """Should handle large hour values."""
        assert format_time(86400) == "24:00:00"  # 24 hours


class TestFormatterConfig:
    """Tests for FormatterConfig dataclass."""

    def test_default_values(self):
        """Should have correct default values."""
        config = FormatterConfig()
        assert config.line_width == 80
        assert config.blank_line_between_speakers is True

    def test_custom_values(self):
        """Should accept custom values."""
        config = FormatterConfig(
            line_width=100, blank_line_between_speakers=False
        )
        assert config.line_width == 100
        assert config.blank_line_between_speakers is False


class TestFormatDiarizedSegments:
    """Tests for format_diarized_segments function."""

    def test_empty_segments_returns_empty(self):
        """Empty segment list should return empty string."""
        assert format_diarized_segments([]) == ""

    def test_single_speaker_single_segment(self):
        """Single speaker with one segment should format correctly."""
        segments = [
            MockSpeakerSegment(
                start=0.0, end=5.0, text="Hello world.", speaker="SPEAKER_00"
            )
        ]
        result = format_diarized_segments(segments)
        assert "[SPEAKER_00]" in result
        assert "Hello world." in result

    def test_single_speaker_multiple_segments(self):
        """Same speaker segments should be combined."""
        segments = [
            MockSpeakerSegment(
                start=0.0, end=2.0, text="Hello.", speaker="SPEAKER_00"
            ),
            MockSpeakerSegment(
                start=2.0, end=5.0, text="World.", speaker="SPEAKER_00"
            ),
        ]
        result = format_diarized_segments(segments)
        # Should only have one speaker header
        assert result.count("[SPEAKER_00]") == 1
        # Both texts should be present
        assert "Hello." in result
        assert "World." in result

    def test_speaker_change_creates_new_block(self):
        """Speaker change should create new paragraph."""
        segments = [
            MockSpeakerSegment(
                start=0.0, end=2.0, text="Hello.", speaker="SPEAKER_00"
            ),
            MockSpeakerSegment(
                start=2.0, end=5.0, text="Hi there.", speaker="SPEAKER_01"
            ),
        ]
        result = format_diarized_segments(segments)
        assert "[SPEAKER_00]" in result
        assert "[SPEAKER_01]" in result
        # Should have blank line between speakers (default)
        assert "\n\n" in result

    def test_no_blank_line_between_speakers(self):
        """Should respect blank_line_between_speakers=False."""
        segments = [
            MockSpeakerSegment(
                start=0.0, end=2.0, text="Hello.", speaker="SPEAKER_00"
            ),
            MockSpeakerSegment(
                start=2.0, end=5.0, text="Hi there.", speaker="SPEAKER_01"
            ),
        ]
        config = FormatterConfig(blank_line_between_speakers=False)
        result = format_diarized_segments(segments, config=config)
        # Should not have double newline
        assert "\n\n" not in result

    def test_includes_timestamps_when_requested(self):
        """Should include timestamps in speaker header."""
        segments = [
            MockSpeakerSegment(
                start=65.0, end=70.0, text="Hello.", speaker="SPEAKER_00"
            )
        ]
        result = format_diarized_segments(segments, include_timestamps=True)
        assert "[SPEAKER_00] (01:05)" in result

    def test_timestamps_with_hours(self):
        """Should format hour timestamps correctly."""
        segments = [
            MockSpeakerSegment(
                start=3661.0, end=3670.0, text="Hello.", speaker="SPEAKER_00"
            )
        ]
        result = format_diarized_segments(segments, include_timestamps=True)
        assert "(01:01:01)" in result

    def test_filters_empty_segments(self):
        """Segments with empty text should be filtered."""
        segments = [
            MockSpeakerSegment(
                start=0.0, end=2.0, text="Hello.", speaker="SPEAKER_00"
            ),
            MockSpeakerSegment(
                start=2.0, end=3.0, text="   ", speaker="SPEAKER_00"
            ),
            MockSpeakerSegment(
                start=3.0, end=5.0, text="World.", speaker="SPEAKER_00"
            ),
        ]
        result = format_diarized_segments(segments)
        assert "Hello." in result
        assert "World." in result

    def test_wraps_long_text(self):
        """Long text should be wrapped."""
        long_text = "word " * 30  # ~150 chars
        segments = [
            MockSpeakerSegment(
                start=0.0, end=10.0, text=long_text, speaker="SPEAKER_00"
            )
        ]
        result = format_diarized_segments(segments)
        lines = result.split("\n")
        # First line is speaker header, subsequent lines are wrapped text
        text_lines = [ln for ln in lines if not ln.startswith("[")]
        assert all(len(line) <= DEFAULT_LINE_WIDTH for line in text_lines)

    def test_custom_line_width(self):
        """Should respect custom line width."""
        long_text = "word " * 30
        segments = [
            MockSpeakerSegment(
                start=0.0, end=10.0, text=long_text, speaker="SPEAKER_00"
            )
        ]
        config = FormatterConfig(line_width=40)
        result = format_diarized_segments(segments, config=config)
        lines = result.split("\n")
        text_lines = [ln for ln in lines if not ln.startswith("[")]
        assert all(len(line) <= 40 for line in text_lines)


class TestFormatSimpleSegments:
    """Tests for format_simple_segments function."""

    def test_empty_segments_returns_empty(self):
        """Empty segment list should return empty string."""
        assert format_simple_segments([]) == ""

    def test_single_segment(self):
        """Single segment should format correctly."""
        segments = [MockSegment(start=0.0, end=5.0, text="Hello world.")]
        result = format_simple_segments(segments)
        assert result == "Hello world."

    def test_multiple_segments_combined(self):
        """Multiple segments should be combined."""
        segments = [
            MockSegment(start=0.0, end=2.0, text="Hello."),
            MockSegment(start=2.0, end=5.0, text="World."),
        ]
        result = format_simple_segments(segments)
        assert "Hello." in result
        assert "World." in result

    def test_wraps_long_text(self):
        """Long combined text should be wrapped."""
        long_text = "word " * 30
        segments = [MockSegment(start=0.0, end=10.0, text=long_text)]
        result = format_simple_segments(segments)
        lines = result.split("\n")
        assert all(len(line) <= DEFAULT_LINE_WIDTH for line in lines)

    def test_with_timestamps_each_segment_on_line(self):
        """With timestamps, each segment gets its own line."""
        segments = [
            MockSegment(start=0.0, end=2.0, text="Hello."),
            MockSegment(start=65.0, end=70.0, text="World."),
        ]
        result = format_simple_segments(segments, include_timestamps=True)
        assert "[00:00]" in result
        assert "[01:05]" in result
        assert "Hello." in result
        assert "World." in result

    def test_timestamps_with_hours(self):
        """Should format hour timestamps correctly."""
        segments = [MockSegment(start=3661.0, end=3670.0, text="Hello.")]
        result = format_simple_segments(segments, include_timestamps=True)
        assert "[01:01:01]" in result

    def test_filters_empty_segments(self):
        """Segments with empty text should be filtered."""
        segments = [
            MockSegment(start=0.0, end=2.0, text="Hello."),
            MockSegment(start=2.0, end=3.0, text="   "),
            MockSegment(start=3.0, end=5.0, text="World."),
        ]
        result = format_simple_segments(segments)
        assert "Hello." in result
        assert "World." in result

    def test_custom_line_width(self):
        """Should respect custom line width."""
        long_text = "word " * 30
        segments = [MockSegment(start=0.0, end=10.0, text=long_text)]
        config = FormatterConfig(line_width=40)
        result = format_simple_segments(segments, config=config)
        lines = result.split("\n")
        assert all(len(line) <= 40 for line in lines)

    def test_timestamps_with_long_text_wraps(self):
        """Timestamped segments with long text should wrap with indentation."""
        long_text = "word " * 20  # ~100 chars
        segments = [MockSegment(start=0.0, end=10.0, text=long_text)]
        result = format_simple_segments(segments, include_timestamps=True)
        lines = result.split("\n")
        # All lines should respect width
        assert all(len(line) <= DEFAULT_LINE_WIDTH for line in lines)


class TestDefaultLineWidth:
    """Tests for DEFAULT_LINE_WIDTH constant."""

    def test_default_width_is_80(self):
        """Default line width should be 80."""
        assert DEFAULT_LINE_WIDTH == 80
