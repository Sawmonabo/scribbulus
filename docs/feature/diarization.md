---
feature: diarization
status: stable
since: v0.1.0
updated: 2025-12-20
---

# Speaker Diarization

## Overview

Speaker diarization identifies and labels different speakers in a transcript.
Scribbulus uses WhisperX with pyannote for speaker identification, enabling
transcripts that show who said what. This is particularly useful for
interviews, meetings, and multi-speaker recordings.

## Quick Start

```bash
# Enable diarization (requires HuggingFace token)
export HF_TOKEN=your_huggingface_token
scribbulus transcribe meeting.mp4
```

## Usage

### Prerequisites

Speaker diarization requires:

1. A HuggingFace account and access token
2. Acceptance of the pyannote model terms on HuggingFace:
   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### Setting Up

1. Create a HuggingFace account at <https://huggingface.co>
2. Generate an access token at <https://huggingface.co/settings/tokens>
3. Accept the model terms for pyannote models (links above)
4. Set your token:

```bash
# Via environment variable (recommended)
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx

# Or via command line
scribbulus transcribe meeting.mp4 --hf-token hf_xxxxxxxxxxxxxxxxxxxxx
```

### Basic Usage

With the token set, diarization is enabled by default:

```bash
scribbulus transcribe interview.mp4 -o interview.txt
```

Output:

```text
[SPEAKER_00]
Hello everyone, thank you for joining today's meeting. I wanted to discuss the
quarterly results.

[SPEAKER_01]
Thanks for the overview. I have a few questions about the revenue projections.
```

### Disabling Diarization

If you don't need speaker labels:

```bash
scribbulus transcribe recording.mp4 --no-diarization
```

### Specifying Number of Speakers

If you know how many speakers are in the recording:

```bash
scribbulus transcribe meeting.mp4 --num-speakers 3
```

This can improve accuracy when the number of speakers is known in advance.

### Including Timestamps

Add timestamps to speaker segments:

```bash
scribbulus transcribe meeting.mp4 --timestamps
```

Output:

```text
[SPEAKER_00] (00:00)
Hello everyone, thank you for joining today's meeting.

[SPEAKER_01] (00:15)
Thanks for the overview. I have a few questions.
```

## Configuration

| Option             | Default     | Description                   |
| ------------------ | ----------- | ----------------------------- |
| `--hf-token`       | `$HF_TOKEN` | HuggingFace access token      |
| `--no-diarization` | false       | Disable speaker identification|
| `--num-speakers`   | auto        | Number of speakers (if known) |
| `--timestamps`     | false       | Include timestamps in output  |

## Limitations

- **HuggingFace token required**: Cannot run without accepting model terms
- **Additional memory**: Diarization adds ~2GB VRAM usage
- **Processing time**: Adds overhead to transcription time
- **Speaker accuracy**: May occasionally mis-label speakers in complex scenarios
- **Maximum speakers**: Works best with fewer than 10 distinct speakers

## Related Documents

- [Feature: Transcription](./transcription.md) - Core transcription feature
- [Feature: Output Formats](./output-formats.md) - Output formatting options
- [ADR-002: Diarization](../architecture/adr/002-diarization.md)
- [Research: Diarization Guide](../research/diarization-guide.md)
