# FFmpeg Audio Extraction Best Practices

## Overview

This document covers best practices for extracting audio from video files using FFmpeg, with focus on iPhone recordings and large file handling.

## Audio Extraction Commands

### Stream Copy (Fastest, Lossless)

When the source audio codec is compatible with the output container:

```bash
# Basic stream copy - preserves original quality
ffmpeg -i input.mp4 -vn -acodec copy output.m4a

# Using shorthand
ffmpeg -i input.mp4 -vn -c:a copy output.m4a

# Extract specific audio stream
ffmpeg -i video.mkv -map 0:a -c:a copy audio.m4a
```

**Key flags:**

- `-vn` - Disable video (no video output)
- `-acodec copy` or `-c:a copy` - Stream copy, no re-encoding
- `-map 0:a` - Select all audio streams from first input

### Transcoding to Different Formats

#### WAV (Optimal for Speech Recognition)

```bash
# 16-bit WAV at 16kHz mono (optimal for STT)
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav

# 24-bit WAV at 48kHz (professional quality)
ffmpeg -i input.mp4 -vn -acodec pcm_s24le -ar 48000 output.wav
```

#### MP3 (LAME Encoder)

```bash
# VBR quality mode (recommended) - scale 0-9, lower = better
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3

# CBR mode - fixed bitrate
ffmpeg -i input.mp4 -vn -c:a libmp3lame -b:a 320k output.mp3
```

#### AAC/M4A

```bash
# Native AAC encoder
ffmpeg -i input.mp4 -vn -c:a aac -b:a 192k output.m4a

# VBR mode
ffmpeg -i input.mp4 -vn -c:a aac -q:a 2 output.m4a
```

#### FLAC (Lossless)

```bash
# Default compression
ffmpeg -i input.mp4 -vn -c:a flac output.flac

# Maximum compression (level 12)
ffmpeg -i input.mp4 -vn -c:a flac -compression_level 8 output.flac
```

## iPhone .MOV/.MP4 Specifics

### Common iPhone Audio Specifications

| Recording Mode | Container | Audio Codec | Sample Rate | Channels |
|---------------|-----------|-------------|-------------|----------|
| Standard video | MOV/MP4 | AAC-LC | 48kHz | Stereo |
| 4K video | MOV/MP4 | AAC-LC | 48kHz | Stereo |
| Live Photos | MOV | PCM | 44.1kHz | Mono/Stereo |
| ProRes | MOV | PCM (LPCM) | 48kHz | Stereo |
| Slow-motion | MOV/MP4 | AAC-LC | 48kHz | Stereo |

### Handling Variable Frame Rate (VFR)

iPhone videos often use VFR which can cause audio sync issues:

```bash
# Add genpts flag to handle VFR
ffmpeg -fflags +genpts -i input.mov -vn -c:a copy output.m4a

# Force audio sync correction
ffmpeg -i input.mov -vn -async 1 -c:a aac -b:a 192k output.m4a

# Full resync for severe issues
ffmpeg -fflags +genpts+igndts -i input.mov -vn -async 1 -c:a copy output.m4a
```

## Large File Handling

### Streaming/Memory-Efficient Processing

```bash
# Extract chunk without decoding entire file (-ss before -i)
ffmpeg -ss 60 -i input.mp4 -t 30 -vn -c:a pcm_s16le chunk.wav

# Limit buffer size
ffmpeg -i input.mp4 -vn -bufsize 512k -c:a aac output.m4a

# Limit threads to reduce memory
ffmpeg -i input.mp4 -vn -threads 2 -c:a aac output.m4a
```

### Progress Reporting

```bash
# Progress to stdout (for parsing)
ffmpeg -i input.mp4 -vn -c:a aac -progress pipe:1 output.m4a

# Show stats during encoding
ffmpeg -i input.mp4 -vn -c:a aac -stats output.m4a
```

## Using ffprobe for Input Validation

```bash
# Get all stream info in JSON
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4

# Get just audio stream info
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels,bit_rate -of json input.mp4

# Check if file has audio
ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 input.mp4

# Get duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
```

## Cross-Platform Installation

### macOS

```bash
brew install ffmpeg
```

### Ubuntu/Debian

```bash
sudo apt update && sudo apt install ffmpeg
```

### Fedora

```bash
sudo dnf install ffmpeg
```

### Verify Installation

```bash
ffmpeg -version
ffprobe -version
```

## Quick Reference

```bash
# Stream copy (fastest, lossless)
ffmpeg -i input.mp4 -vn -c:a copy output.m4a

# Optimal for STT (16kHz mono WAV)
ffmpeg -i input.mp4 -vn -c:a pcm_s16le -ar 16000 -ac 1 output.wav

# High-quality MP3
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3

# iPhone VFR fix
ffmpeg -fflags +genpts -i input.mov -vn -c:a copy output.m4a

# Extract time range
ffmpeg -i input.mp4 -ss 00:01:00 -to 00:02:00 -vn -c:a copy output.m4a
```

## Sources

- [FFmpeg Official Documentation](https://ffmpeg.org/ffmpeg.html)
- [FFmpeg Codecs Documentation](https://ffmpeg.org/ffmpeg-codecs.html)
- [FFprobe Documentation](https://ffmpeg.org/ffprobe.html)
