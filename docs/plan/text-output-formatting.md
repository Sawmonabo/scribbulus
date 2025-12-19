# Text Output Formatting

## Summary

Improve transcript output formatting to be page-friendly and readable with proper
line wrapping and speaker separation, instead of producing one long continuous
line.

## Problem Statement

Currently, transcript segments are joined with spaces (`" ".join(texts)`),
creating output that is difficult to read in terminals, editors, and pagers:

```text
[Speaker_0] Hello everyone, thank you for joining today's meeting. I wanted to discuss the quarterly results. [Speaker_1] Thanks for the overview. I have questions about the projections.
```

## Goals

1. Produce readable output when viewed in editors, terminals, and pagers
2. Apply sensible line wrapping (80 characters)
3. Separate speaker segments clearly
4. Centralize formatting logic in a reusable module

## Non-Goals

- Configurable line width via CLI option (future enhancement)
- Alternative output formats (JSON, SRT, VTT)
- Paragraph detection based on silence gaps

## Design Decisions

| Decision           | Choice                    | Rationale                                      |
| ------------------ | ------------------------- | ---------------------------------------------- |
| Line width         | 80 characters             | Standard terminal width, widely readable       |
| Segment separation | Newline on speaker change | Balances readability with compactness          |
| Long words         | Preserve intact           | Avoid breaking URLs, technical terms           |
| Code location      | `utils/formatter.py`      | Reusable, testable, follows existing structure |
| Between speakers   | Blank line                | Visual separation improves scannability        |

## Desired Output Format

### With Diarization

```text
[SPEAKER_00]
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results and our plans for the next quarter.

[SPEAKER_01]
Thanks for the overview. I have a few questions about the revenue projections
that were mentioned in the slides.
```

### With Diarization and Timestamps

```text
[SPEAKER_00] (00:00)
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results and our plans for the next quarter.

[SPEAKER_01] (00:15)
Thanks for the overview. I have a few questions about the revenue projections
that were mentioned in the slides.
```

### Without Diarization

```text
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results and our plans for the next quarter. Thanks for the overview. I
have a few questions about the revenue projections that were mentioned in the
slides.
```

## Architecture

```text
┌─────────────────┐     ┌──────────────────────┐
│ transcribe.py   │────>│ TranscriptionOutput  │
│ (CLI)           │     │ .format_transcript() │
└─────────────────┘     └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    v                             v
        ┌───────────────────┐       ┌───────────────────────┐
        │ format_diarized   │       │ format_simple         │
        │ _transcript()     │       │ _segments()           │
        │ (diarization.py)  │       │ (engine.py)           │
        └─────────┬─────────┘       └───────────┬───────────┘
                  │                             │
                  └─────────────┬───────────────┘
                                │
                                v
                  ┌─────────────────────────┐
                  │ utils/formatter.py      │
                  │ - wrap_text()           │
                  │ - format_time()         │
                  │ - format_diarized_      │
                  │   segments()            │
                  │ - format_simple_        │
                  │   segments()            │
                  └─────────────────────────┘
```

## Implementation

### New Module: `src/scribbulus/utils/formatter.py`

Core functions:

- `wrap_text(text, width)` - Wrap text to specified width using `textwrap.fill()`
- `format_time(seconds)` - Format seconds as MM:SS or HH:MM:SS
- `format_diarized_segments(segments, include_timestamps, config)` - Format
  speaker-labeled segments
- `format_simple_segments(segments, include_timestamps, config)` - Format
  segments without speaker labels
- `FormatterConfig` - Dataclass for configuration options

### Integration Points

1. `diarization.py:format_diarized_transcript()` delegates to
   `format_diarized_segments()`
2. `engine.py:TranscriptionOutput.format_transcript()` uses
   `format_simple_segments()` for non-diarized output

## Edge Cases

| Case                        | Handling                                    |
| --------------------------- | ------------------------------------------- |
| Very long words (>80 chars) | Preserved intact (`break_long_words=False`) |
| Empty segments              | Filtered out                                |
| Single speaker              | Formats correctly with wrapping             |
| No segments                 | Returns empty string                        |
| Unicode text                | Handled by Python's textwrap                |

## Backwards Compatibility

- Public function signatures in `diarization.py` and `engine.py` unchanged
- CLI options (`--timestamps`, `--no-speakers`) continue to work
- Only output format changes (the intended improvement)

## Related Files

- `src/scribbulus/utils/formatter.py` - New formatter module
- `src/scribbulus/transcription/diarization.py` - Diarized output formatting
- `src/scribbulus/transcription/engine.py` - TranscriptionOutput class
- `src/scribbulus/cli/transcribe.py` - CLI entrypoint
- `tests/unit/test_formatter.py` - Unit tests
