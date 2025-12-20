---
adr: 002
status: accepted
date: 2025-12-14
supersedes: []
superseded_by: []
---

# ADR-002: Use WhisperX for Speaker Diarization

## Status

accepted - 2025-12-14

## Context

Speaker diarization (identifying "who spoke when") is a valuable feature for
meeting transcriptions, interviews, and multi-speaker recordings. Options
include:

- WhisperX (integrates pyannote with Whisper)
- pyannote.audio directly
- Resemblyzer + clustering
- Cloud APIs (AssemblyAI, Google)

Key requirements:

- Accurate speaker identification
- Integration with Whisper transcription
- Word-level speaker alignment
- Local processing capability

## Decision

Use **WhisperX** with pyannote for speaker diarization.

WhisperX provides:

- State-of-the-art speaker diarization via pyannote
- Word-level alignment between transcription and speakers
- Seamless integration with Whisper transcription output
- Active maintenance and good documentation

## Consequences

### Positive

- **Accuracy**: pyannote provides best-in-class speaker separation
- **Integration**: Designed to work with Whisper output
- **Word alignment**: Can attribute individual words to speakers
- **Local processing**: No cloud dependency once models are downloaded

### Negative

- **HuggingFace token required**: Users must create account and accept model
  terms
- **Additional memory**: Adds ~2GB VRAM usage
- **Processing time**: Adds overhead to transcription pipeline
- **Model access**: pyannote models require explicit agreement to terms

### Neutral

- Different speaker labels per session (SPEAKER_00, SPEAKER_01)
- Requires torch/torchaudio (already needed for faster-whisper)

## Research References

- [Research: Diarization Guide](../../research/diarization-guide.md) -
  Comprehensive diarization setup and usage guide

## Related Documents

- [Feature: Diarization](../../feature/diarization.md) - User documentation
- [Component: Transcription Engine](../components/transcription-engine.md)
