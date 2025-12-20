---
component: media-processor
updated: 2025-12-20
---

# Media Processor

## Purpose

The media processor handles format detection and audio extraction from video
files. It uses FFmpeg for all media operations, ensuring broad format support
and reliable audio extraction.

## Location

- Source: `src/scribbulus/media/`
- Tests: `tests/unit/test_formats.py`, `tests/unit/test_audio_prep.py`

## Interface

### Format Detection

```python
from scribbulus.media import detect_format, MediaInfo

info: MediaInfo = detect_format("video.mp4")
# MediaInfo(
#     path="video.mp4",
#     format="mp4",
#     has_audio=True,
#     duration=120.5,
#     audio_codec="aac",
#     ...
# )
```

### Audio Extraction

```python
from scribbulus.media import extract_audio

wav_path = extract_audio(
    input_path="video.mp4",
    output_path="audio.wav",  # Optional
    sample_rate=16000
)
```

## Dependencies

| Dependency | Purpose                |
| ---------- | ---------------------- |
| FFmpeg     | Audio/video processing |
| ffprobe    | Format detection       |

## Internal Design

### Module Structure

```text
media/
├── __init__.py     # Public exports
├── ffmpeg.py       # FFmpeg discovery and execution
├── formats.py      # Format detection with ffprobe
└── audio_prep.py   # Audio extraction and conversion
```

### FFmpeg Integration

FFmpeg is invoked via subprocess with:

- **No shell=True**: Security best practice
- **List arguments**: Prevents command injection
- **Explicit paths**: FFmpeg binary discovered at startup

### Supported Formats

**Audio**:

- WAV (recommended for processing)
- MP3, M4A, FLAC, OGG, AAC

**Video**:

- MP4, MOV (including iPhone recordings)
- MKV, AVI, WebM

### Audio Extraction Process

1. Detect input format with ffprobe
2. Verify audio stream exists
3. Extract audio to WAV (16kHz, mono)
4. Return path to extracted audio

### Error Handling

- `FFmpegNotFoundError`: FFmpeg not installed
- `NoAudioStreamError`: Input file has no audio
- `UnsupportedFormatError`: Format not recognized

## Related Documents

- [Feature: Transcription](../../feature/transcription.md) - Supported formats
- [Research: FFmpeg Audio Extraction](../../research/ffmpeg-audio-extraction.md)
