# Scribbulus

[![CI](https://github.com/Sawmonabo/scribbulus/actions/workflows/ci.yml/badge.svg)](https://github.com/Sawmonabo/scribbulus/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Sawmonabo/scribbulus/graph/badge.svg)](https://codecov.io/gh/Sawmonabo/scribbulus)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg?logo=conventionalcommits)](https://conventionalcommits.org)

Production-grade media transcription tool that converts audio and video files to text using faster-whisper with optional speaker diarization.

## Features

- **Multi-format Support**: Process video (MP4, MOV, MKV, AVI, WebM) and audio (WAV, MP3, M4A, FLAC, OGG, AAC) files
- **High-Quality Transcription**: Powered by faster-whisper with large-v3-turbo model (4x faster than OpenAI Whisper)
- **Speaker Diarization**: Identify and label different speakers using WhisperX and pyannote
- **Memory Efficient**: Stream-based processing for large files without loading everything into RAM
- **Cross-Platform**: Works on macOS and Linux with automatic dependency detection
- **Language Detection**: Automatic language detection or manual specification

## Installation

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/Sawmonabo/scribbulus.git
cd scribbulus

# Install everything (auto-detects your OS)
make install
```

This will:

1. Install `uv` package manager (if not present)
2. Install FFmpeg via your system package manager
3. Install Python dependencies

### Manual Installation

1. **Install uv** (Python package manager):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install FFmpeg**:

   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - Fedora: `sudo dnf install ffmpeg`

3. **Install scribbulus**:
   ```bash
   uv sync
   uv pip install -e .
   ```

### GPU Acceleration (Optional)

For faster transcription, install CUDA support:

1. Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. The tool will automatically use GPU when available

### Speaker Diarization Setup

Speaker diarization requires a HuggingFace token:

1. Create a HuggingFace account at https://huggingface.co
2. Get your token at https://huggingface.co/settings/tokens
3. Accept the terms for pyannote models:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
4. Set the token:
   ```bash
   export HF_TOKEN=your_token_here
   ```

## Usage

### Basic Transcription

```bash
# Transcribe a video file (output to stdout)
scribbulus-transcribe video.mp4

# Save output to a file
scribbulus-transcribe video.mp4 -o transcript.txt

# Transcribe audio file
scribbulus-transcribe podcast.mp3 -o transcript.txt
```

### With Speaker Diarization

```bash
# Requires HF_TOKEN to be set
scribbulus-transcribe interview.mp4 -o transcript.txt

# Specify number of speakers for better accuracy
scribbulus-transcribe meeting.mp4 --num-speakers 3 -o transcript.txt
```

### Performance Options

```bash
# Use a smaller, faster model
scribbulus-transcribe audio.mp3 --model small

# Disable diarization for faster processing
scribbulus-transcribe audio.mp3 --no-diarization

# Force CPU inference
scribbulus-transcribe audio.mp3 --device cpu
```

### Advanced Options

```bash
# Specify language (skip auto-detection)
scribbulus-transcribe audio.mp3 -l en

# Include timestamps in output
scribbulus-transcribe audio.mp3 --timestamps

# Verbose output with progress details
scribbulus-transcribe audio.mp3 -v
```

### Full CLI Reference

```
Usage: scribbulus-transcribe [OPTIONS] INPUT_PATH

  Transcribe audio/video files to text.

Options:
  -o, --output PATH              Output .txt file path
  -l, --language TEXT            Language code (auto-detect if not set)
  --model [tiny|base|small|medium|large-v3|large-v3-turbo]
                                 Whisper model size
  --device [auto|cuda|cpu]       Device for inference
  --compute-type [float16|float32|int8_float16|int8|auto]
                                 Compute type for model
  --no-diarization               Disable speaker diarization
  --num-speakers INTEGER         Number of speakers (if known)
  --hf-token TEXT                HuggingFace token for diarization
  --timestamps                   Include timestamps in output
  --no-speakers                  Exclude speaker labels from output
  --chunk-duration FLOAT         Duration of audio chunks (seconds)
  --no-chunking                  Disable chunking
  -v, --verbose                  Enable verbose output
  --version                      Show version
  --help                         Show this message and exit
```

## Supported Formats

### Video

| Format | Extension | Notes                          |
| ------ | --------- | ------------------------------ |
| MP4    | .mp4      | Most common, H.264/AAC         |
| MOV    | .mov      | Apple QuickTime, iPhone videos |
| MKV    | .mkv      | Matroska container             |
| AVI    | .avi      | Legacy Windows format          |
| WebM   | .webm     | Web-optimized                  |

### Audio

| Format | Extension | Notes                         |
| ------ | --------- | ----------------------------- |
| WAV    | .wav      | Uncompressed, optimal for STT |
| MP3    | .mp3      | Most compatible lossy         |
| M4A    | .m4a      | Apple/AAC audio               |
| FLAC   | .flac     | Lossless compressed           |
| OGG    | .ogg      | Open source lossy             |
| AAC    | .aac      | Advanced Audio Coding         |

## Model Sizes

| Model          | Parameters | VRAM (GPU) | Speed     | Accuracy  |
| -------------- | ---------- | ---------- | --------- | --------- |
| tiny           | 39M        | ~1GB       | Fastest   | Basic     |
| base           | 74M        | ~1GB       | Very Fast | Good      |
| small          | 244M       | ~2GB       | Fast      | Better    |
| medium         | 769M       | ~5GB       | Moderate  | Great     |
| large-v3       | 1550M      | ~10GB      | Slow      | Best      |
| large-v3-turbo | 809M       | ~6GB       | Fast      | Excellent |

**Recommended**: `large-v3-turbo` offers the best balance of speed and accuracy.

## Output Format

### With Speaker Diarization

```
[Speaker 1] Hello, welcome to today's meeting.
[Speaker 2] Thanks for having me. Let's discuss the project timeline.
[Speaker 1] Sure. I think we should start with the requirements phase.
```

### Without Diarization

```
Hello, welcome to today's meeting. Thanks for having me. Let's discuss the project timeline. Sure. I think we should start with the requirements phase.
```

### With Timestamps

```
[00:00] [Speaker 1] Hello, welcome to today's meeting.
[00:05] [Speaker 2] Thanks for having me.
```

## Development

### Setup Development Environment

```bash
make dev
```

### Run Tests

```bash
make test
```

### Lint and Format

```bash
make lint    # Check for issues
make format  # Auto-format code
```

### Clean Build Artifacts

```bash
make clean
```

## System Requirements

- Python 3.13+
- FFmpeg
- ~6GB VRAM for GPU inference (large-v3-turbo)
- ~4GB RAM for CPU inference

## Troubleshooting

### FFmpeg Not Found

```
Error: FFmpeg not found

Install ffmpeg:
  macOS: brew install ffmpeg
  Ubuntu/Debian: sudo apt install ffmpeg
  Fedora: sudo dnf install ffmpeg
```

### CUDA Out of Memory

Try a smaller model or use CPU:

```bash
scribbulus-transcribe audio.mp3 --model small
# or
scribbulus-transcribe audio.mp3 --device cpu
```

### Diarization Not Working

1. Ensure HF_TOKEN is set correctly
2. Accept the pyannote model terms on HuggingFace
3. Check your internet connection (models download on first use)

### Slow Transcription

1. Use GPU if available (`--device cuda`)
2. Use a smaller model (`--model small`)
3. Disable diarization (`--no-diarization`)

## Architecture

```
scribbulus/
├── cli/
│   └── transcribe.py      # CLI entrypoint
├── media/
│   ├── ffmpeg.py          # FFmpeg discovery & helpers
│   ├── audio_prep.py      # Audio extraction & preprocessing
│   └── formats.py         # Format detection & validation
├── transcription/
│   ├── engine.py          # Main orchestration pipeline
│   ├── whisper_backend.py # faster-whisper integration
│   ├── diarization.py     # Speaker diarization
│   └── chunking.py        # Memory-efficient chunking
└── utils/
    └── errors.py          # Custom exceptions
```

## License

MIT License

## Acknowledgments

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - CTranslate2-based Whisper implementation
- [WhisperX](https://github.com/m-bain/whisperX) - Word-level timestamps and diarization
- [pyannote-audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization models
