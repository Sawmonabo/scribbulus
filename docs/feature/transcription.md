---
feature: transcription
status: stable
since: v0.1.0
updated: 2025-12-20
---

# Transcription

## Overview

Scribbulus transcribes audio and video files to text using OpenAI's Whisper
model via the faster-whisper implementation. It supports automatic language
detection, multiple model sizes, and handles files of any length through
memory-efficient chunked processing.

## Quick Start

```bash
# Basic transcription
scribbulus transcribe recording.mp4

# Save to file
scribbulus transcribe recording.mp4 -o transcript.txt

# Specify language
scribbulus transcribe recording.mp4 -l en
```

## Usage

### Basic Usage

Transcribe any supported audio or video file:

```bash
scribbulus transcribe INPUT_FILE
```

Output is written to stdout by default, or to a file with `-o`:

```bash
scribbulus transcribe interview.mp3 -o interview.txt
```

### Supported Formats

**Audio**: WAV, MP3, M4A, FLAC, OGG, AAC

**Video**: MP4, MOV, MKV, AVI, WebM

### Model Selection

Choose a Whisper model based on your accuracy/speed requirements:

```bash
# Use a smaller, faster model
scribbulus transcribe recording.mp4 --model small

# Use the default high-accuracy model
scribbulus transcribe recording.mp4 --model large-v3-turbo
```

| Model          | Size | Speed   | Accuracy | VRAM  |
| -------------- | ---- | ------- | -------- | ----- |
| tiny           | 39M  | Fastest | Basic    | ~1GB  |
| base           | 74M  | Fast    | Good     | ~1GB  |
| small          | 244M | Medium  | Better   | ~2GB  |
| medium         | 769M | Slow    | Great    | ~5GB  |
| large-v3-turbo | 809M | Medium  | Best     | ~6GB  |

### Language Detection

By default, Scribbulus auto-detects the spoken language. You can also specify
it explicitly:

```bash
# Auto-detect (default)
scribbulus transcribe recording.mp4

# Specify language
scribbulus transcribe recording.mp4 -l es  # Spanish
scribbulus transcribe recording.mp4 -l fr  # French
scribbulus transcribe recording.mp4 -l de  # German
```

Supported languages include all languages supported by Whisper (99+ languages).

### Verbose Output

Enable verbose mode for progress details:

```bash
scribbulus transcribe recording.mp4 -v
```

## Configuration

| Option           | Default        | Description               |
| ---------------- | -------------- | ------------------------- |
| `-o, --output`   | stdout         | Output file path          |
| `-l, --language` | auto           | Language code (ISO 639-1) |
| `--model`        | large-v3-turbo | Whisper model to use      |
| `-v, --verbose`  | false          | Enable verbose output     |

## Limitations

- **DRM-protected content**: Cannot process encrypted media files
- **GPU recommended**: CPU transcription works but is significantly slower
- **Large files**: Very long files (>2 hours) work but take time
- **Background noise**: Heavy background noise may reduce accuracy

## Related Documents

- [Feature: Diarization](./diarization.md) - Speaker identification
- [Feature: Output Formats](./output-formats.md) - Output formatting options
- [Architecture: Transcription Engine](../architecture/components/transcription-engine.md)
- [ADR-001: Whisper Engine](../architecture/adr/001-whisper-engine.md)
- [Research: Whisper Models](../research/whisper-models.md)
- [Research: Speech-to-Text Options](../research/speech-to-text-options.md)
