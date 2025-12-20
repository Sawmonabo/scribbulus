# Whisper Model Comparison

## Overview

OpenAI Whisper offers multiple model sizes with different speed/accuracy tradeoffs.

## Model Sizes

| Model              | Parameters | VRAM Required | Relative Speed | English WER |
| ------------------ | ---------- | ------------- | -------------- | ----------- |
| tiny               | 39M        | ~1GB          | ~10x           | ~10%        |
| base               | 74M        | ~1GB          | ~7x            | ~7%         |
| small              | 244M       | ~2GB          | ~4x            | ~5%         |
| medium             | 769M       | ~5GB          | ~2x            | ~4%         |
| large-v3           | 1.55B      | ~10GB         | 1x             | ~3%         |
| **large-v3-turbo** | 809M       | ~6GB          | **~8x**        | ~3.5%       |

WER = Word Error Rate (lower is better)

## large-v3-turbo (Recommended)

Released October 2024, the turbo model is optimized for speed while maintaining accuracy.

**Key Features:**

- Decoder layers reduced from 32 to 4
- ~8x faster than large-v3
- Minimal accuracy degradation for transcription
- 809M parameters (vs 1.55B for large-v3)

**Limitations:**

- Translation quality is reduced compared to large-v3
- Use medium or large-v3 for translation tasks

## Compute Types

### GPU (CUDA)

| Compute Type | Memory Usage | Speed    | Quality |
| ------------ | ------------ | -------- | ------- |
| float16      | Baseline     | Fastest  | Best    |
| int8_float16 | ~50% less    | Fast     | Good    |
| int8         | ~75% less    | Moderate | Good    |

### CPU

| Compute Type | Speed   | Notes               |
| ------------ | ------- | ------------------- |
| int8         | Fastest | Recommended for CPU |
| float32      | Slowest | Not recommended     |

## Usage Examples

### faster-whisper Configuration

```python
from faster_whisper import WhisperModel

# GPU with float16 (recommended for GPU)
model = WhisperModel(
    "large-v3-turbo",
    device="cuda",
    compute_type="float16",
)

# GPU with reduced memory
model = WhisperModel(
    "large-v3-turbo",
    device="cuda",
    compute_type="int8_float16",
)

# CPU optimized
model = WhisperModel(
    "large-v3-turbo",
    device="cpu",
    compute_type="int8",
)

# Auto-detect device
model = WhisperModel(
    "large-v3-turbo",
    device="auto",
)
```

### Transcription Options

```python
segments, info = model.transcribe(
    audio_path,
    language="en",              # or None for auto-detect
    word_timestamps=True,       # Get word-level timing
    vad_filter=True,            # Skip silence
    vad_parameters=dict(
        min_silence_duration_ms=500,
        threshold=0.5,
    ),
    beam_size=5,                # Higher = more accurate, slower
    condition_on_previous_text=True,
)

print(f"Detected language: {info.language}")
print(f"Probability: {info.language_probability:.2%}")
```

## Model Selection Guide

| Use Case              | Recommended Model  | Why                                   |
| --------------------- | ------------------ | ------------------------------------- |
| General transcription | large-v3-turbo     | Best speed/accuracy balance           |
| Low VRAM (<6GB)       | medium or small    | Fits in memory                        |
| CPU only              | small with int8    | Reasonable speed                      |
| Maximum accuracy      | large-v3           | Lowest WER                            |
| Real-time/streaming   | small or base      | Fast enough for real-time             |
| Translation           | large-v3           | Turbo has reduced translation quality |

## Memory Requirements

### GPU VRAM by Model

| Model            | float16 | int8_float16 | int8  |
| ---------------- | ------- | ------------ | ----- |
| tiny             | <1GB    | <1GB         | <1GB  |
| base             | ~1GB    | <1GB         | <1GB  |
| small            | ~2GB    | ~1.5GB       | ~1GB  |
| medium           | ~5GB    | ~3GB         | ~2GB  |
| large-v3         | ~10GB   | ~6GB         | ~4GB  |
| large-v3-turbo   | ~6GB    | ~4GB         | ~3GB  |

### System RAM (CPU inference)

- Add ~2GB to VRAM requirements for system RAM
- INT8 quantization significantly reduces RAM usage

## Sources

- [Whisper large-v3-turbo on Hugging Face](https://huggingface.co/openai/whisper-large-v3-turbo)
- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [faster-whisper Documentation](https://github.com/SYSTRAN/faster-whisper)

## Related Documents

- [ADR-001: Whisper Engine](../architecture/adr/001-whisper-engine.md) - Decision
  to use faster-whisper
- [Feature: Transcription](../feature/transcription.md) - User-facing transcription
  documentation
- [Research: Speech-to-Text Options](./speech-to-text-options.md) - Comparison of
  STT solutions
