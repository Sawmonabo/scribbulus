# Speech-to-Text Options Comparison

## Overview

This document compares local and cloud-based speech-to-text options for audio transcription.

## Local/Offline Options

### 1. faster-whisper (Recommended)

CTranslate2-optimized version of OpenAI Whisper.

**Installation:**

```bash
pip install faster-whisper
```

**Key Benefits:**

- Up to 4x faster than original Whisper with same accuracy
- Lower memory usage
- Supports 8-bit quantization for CPU
- VAD (Voice Activity Detection) filter

**Usage:**

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
segments, info = model.transcribe("audio.mp3", word_timestamps=True)

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

### 2. OpenAI Whisper (Original)

Open source speech recognition model.

**Installation:**

```bash
pip install openai-whisper
```

**Usage:**

```python
import whisper

model = whisper.load_model("large-v3-turbo")
result = model.transcribe("audio.mp3")
print(result["text"])
```

### 3. whisper.cpp (pywhispercpp)

Pure C++ implementation with Python bindings.

**Key Benefits:**

- Extremely fast on CPU
- Low memory footprint
- Apple Silicon optimized

**Installation:**

```bash
pip install pywhispercpp
```

### 4. Vosk

Truly offline speech recognition.

**Key Benefits:**

- Lightweight models (~50MB)
- Works on Raspberry Pi
- Streaming API support
- No internet required

**Installation:**

```bash
pip install vosk
```

## Cloud API Options

### Pricing Comparison (as of 2025)

| Provider | Price/Hour | Diarization | Streaming | Free Tier |
|----------|-----------|-------------|-----------|-----------|
| OpenAI Whisper API | $0.36 | GPT-4o only | No | None |
| Google Cloud | $0.96-1.44 | Included | Yes | 60 min/mo |
| AWS Transcribe | $1.44-1.80 | Included | Yes | 60 min/mo |
| Azure Speech | $1.00-2.10 | Extra cost | Yes | 5 hrs/mo |
| AssemblyAI | $0.15-0.40 | +$0.02/hr | Yes | $50 credit |
| Deepgram | $0.26 | Included | Yes | $200 credit |

### OpenAI Whisper API

```python
from openai import OpenAI

client = OpenAI()

with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"]
    )
```

### AssemblyAI

```python
import assemblyai as aai

aai.settings.api_key = "your-api-key"

config = aai.TranscriptionConfig(
    speaker_labels=True,
    auto_highlights=True,
)

transcriber = aai.Transcriber()
transcript = transcriber.transcribe("audio.mp3", config=config)
```

## Comparison: Local vs Cloud

| Factor | Local (faster-whisper) | Cloud APIs |
|--------|----------------------|------------|
| Cost | Free (after GPU) | Pay per minute |
| Privacy | Full control | Data sent to cloud |
| Speed | Depends on hardware | Generally fast |
| Accuracy | Excellent (~5% WER) | Excellent |
| Setup | More complex | Simple API keys |
| Internet | Not required | Required |
| Scaling | Limited by hardware | Unlimited |

## Recommendation

**For this project: faster-whisper with large-v3-turbo model**

Reasons:

1. Free after initial setup
2. Excellent accuracy (comparable to cloud APIs)
3. Privacy - audio never leaves the machine
4. 4x faster than original Whisper
5. Supports word-level timestamps
6. Works offline

## Sources

- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [faster-whisper PyPI](https://pypi.org/project/faster-whisper/)
- [Vosk Official Website](https://alphacephei.com/vosk/)
- [AssemblyAI Pricing](https://www.assemblyai.com/pricing)
