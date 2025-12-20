---
feature: output-formats
status: stable
since: v0.1.0
updated: 2025-12-20
---

# Output Formats

## Overview

Scribbulus produces readable, well-formatted transcript output. Text is wrapped
at 80 characters for readability, speaker changes are clearly marked with blank
lines, and timestamps can be optionally included.

## Quick Start

```bash
# Default output (readable, wrapped text)
scribbulus transcribe recording.mp4 -o transcript.txt

# With timestamps
scribbulus transcribe recording.mp4 --timestamps -o transcript.txt
```

## Usage

### Default Output Format

The default output is plain text optimized for readability:

- Lines wrapped at 80 characters
- Speaker segments separated by blank lines
- Long words (URLs, technical terms) preserved intact

Example output with diarization:

```text
[SPEAKER_00]
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results and our plans for the next quarter.

[SPEAKER_01]
Thanks for the overview. I have a few questions about the revenue projections
that were mentioned in the slides.
```

### Without Speaker Labels

When diarization is disabled, output is continuous wrapped text:

```text
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results and our plans for the next quarter. Thanks for the overview. I
have a few questions about the revenue projections that were mentioned in the
slides.
```

### With Timestamps

Add `--timestamps` to include timing information:

```text
[SPEAKER_00] (00:00)
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results and our plans for the next quarter.

[SPEAKER_01] (00:15)
Thanks for the overview. I have a few questions about the revenue projections
that were mentioned in the slides.
```

### Output to File

Save output to a file instead of stdout:

```bash
scribbulus transcribe recording.mp4 -o transcript.txt
```

### Piping Output

Output can be piped to other commands:

```bash
# Count words
scribbulus transcribe recording.mp4 | wc -w

# Search for content
scribbulus transcribe recording.mp4 | grep "important topic"
```

## Configuration

| Option          | Default | Description                            |
| --------------- | ------- | -------------------------------------- |
| `-o, --output`  | stdout  | Output file path                       |
| `--timestamps`  | false   | Include segment timestamps             |
| `--no-speakers` | false   | Hide speaker labels (with diarization) |

## Output Specifications

| Property         | Value                     |
| ---------------- | ------------------------- |
| Line width       | 80 characters             |
| Encoding         | UTF-8                     |
| Line endings     | Platform native           |
| Speaker format   | `[SPEAKER_NN]`            |
| Timestamp format | `(MM:SS)` or `(HH:MM:SS)` |

## Limitations

- **Fixed line width**: Currently 80 characters, not configurable
- **Plain text only**: No JSON, SRT, or VTT output (future enhancement)
- **No paragraph detection**: Does not detect natural paragraph breaks

## Related Documents

- [Feature: Transcription](./transcription.md) - Core transcription feature
- [Feature: Diarization](./diarization.md) - Speaker identification
- [Task: Text Output Formatting](../task/text-output-formatting.plan.md) - Implementation details
