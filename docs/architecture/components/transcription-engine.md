---
component: transcription-engine
updated: 2025-12-20
---

# Transcription Engine

## Purpose

The transcription engine orchestrates the speech-to-text pipeline, managing
model loading, audio chunking, transcription, and optional speaker diarization.
It provides a unified interface for converting audio to text.

## Location

- Source: `src/scribbulus/transcription/`
- Tests: `tests/unit/` and `tests/integration/test_transcription.py`

## Interface

### Main Entry Point

```python
from scribbulus.transcription import TranscriptionEngine

engine = TranscriptionEngine(
    model_size="large-v3-turbo",
    device="auto",
    compute_type="auto"
)

result = engine.transcribe(
    audio_path="audio.wav",
    language=None,  # Auto-detect
    diarize=True,
    hf_token="...",
    num_speakers=None  # Auto-detect
)
```

### TranscriptionOutput

```python
@dataclass
class TranscriptionOutput:
    text: str
    segments: list[Segment]
    language: str
    duration: float

    def format_transcript(
        self,
        include_timestamps: bool = False,
        include_speakers: bool = True
    ) -> str:
        ...
```

## Dependencies

| Dependency     | Purpose                       |
| -------------- | ----------------------------- |
| faster-whisper | Speech-to-text transcription  |
| whisperx       | Speaker diarization           |
| torch          | ML framework                  |
| torchaudio     | Audio processing              |

## Internal Design

### Module Structure

```text
transcription/
├── __init__.py         # Public exports
├── engine.py           # TranscriptionEngine class
├── whisper_backend.py  # faster-whisper integration
├── diarization.py      # WhisperX/pyannote integration
└── chunking.py         # Audio chunking for large files
```

### Processing Pipeline

1. **Model Loading** (`whisper_backend.py`): Load faster-whisper model (cached)
2. **Audio Chunking** (`chunking.py`): Split audio into 30-second segments
3. **Transcription** (`whisper_backend.py`): Process each chunk
4. **Diarization** (`diarization.py`): Identify speakers (optional)
5. **Formatting** (`utils/formatter.py`): Format output text

### Memory Management

- Whisper model loaded once and reused
- Audio processed in chunks (30 seconds with 1 second overlap)
- Temporary chunk files cleaned up immediately
- Diarization runs after transcription completes

### Error Handling

- `TranscriptionError`: General transcription failures
- `DiarizationError`: Speaker identification failures
- `AudioProcessingError`: Audio extraction/chunking failures

## Related Documents

- [ADR-001: Whisper Engine](../adr/001-whisper-engine.md) - Engine selection
- [ADR-002: Diarization](../adr/002-diarization.md) - Diarization approach
- [Feature: Transcription](../../feature/transcription.md) - User documentation
- [Feature: Diarization](../../feature/diarization.md) - Diarization docs
