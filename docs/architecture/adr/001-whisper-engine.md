---
adr: 001
status: accepted
date: 2025-12-14
supersedes: []
superseded_by: []
---

# ADR-001: Use faster-whisper for Transcription

## Status

accepted - 2025-12-14

## Context

We need a speech-to-text engine for transcribing audio and video files. The
options include:

- OpenAI Whisper (original implementation)
- faster-whisper (CTranslate2-based reimplementation)
- Cloud APIs (OpenAI, Google, AssemblyAI)
- Alternative local models (Vosk, DeepSpeech)

Key requirements:

- High accuracy across multiple languages
- Local processing (no cloud dependency)
- Reasonable performance on consumer hardware
- Active maintenance and community support

## Decision

Use **faster-whisper** as the transcription engine.

faster-whisper is a CTranslate2-based reimplementation of OpenAI's Whisper that
provides:

- 4x faster transcription than original Whisper
- Lower memory usage (can run large-v3 on 6GB VRAM)
- Same accuracy as original Whisper
- Support for all Whisper model sizes
- Active development and community

## Consequences

### Positive

- **Performance**: 4x faster than original Whisper implementation
- **Memory efficiency**: Can run larger models on consumer GPUs
- **Local processing**: No cloud dependency, works offline
- **Accuracy**: Same high accuracy as OpenAI Whisper
- **Flexibility**: Supports all model sizes from tiny to large-v3-turbo

### Negative

- **CUDA dependency**: Optimal performance requires NVIDIA GPU
- **Model size**: Large models still require significant VRAM/RAM
- **External dependency**: Relies on third-party implementation

### Neutral

- API is slightly different from original Whisper but well-documented
- Model files are downloaded on first use (~3GB for large-v3-turbo)

## Research References

- [Research: Speech-to-Text Options](../../research/speech-to-text-options.md) -
  Comparison of available STT solutions
- [Research: Whisper Models](../../research/whisper-models.md) - Model size and
  performance comparison

## Related Documents

- [Feature: Transcription](../../feature/transcription.md) - User documentation
- [Component: Transcription Engine](../components/transcription-engine.md)
