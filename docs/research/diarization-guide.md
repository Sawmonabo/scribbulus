# Speaker Diarization Guide

## Overview

Speaker diarization identifies "who spoke when" in an audio recording.
This guide covers using WhisperX with pyannote for speaker identification.

## Prerequisites

### HuggingFace Token

Speaker diarization requires access to pyannote models, which need a HuggingFace token.

1. Create account at [huggingface.co](https://huggingface.co)
2. Get token from [Settings > Access Tokens](https://huggingface.co/settings/tokens)
3. Accept terms at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
4. Accept terms at [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

### Installation

```bash
pip install whisperx
```

## WhisperX Diarization Flow

### Complete Pipeline

```python
import whisperx
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"
hf_token = "your_huggingface_token"

# 1. Load audio
audio = whisperx.load_audio("audio.mp3")

# 2. Transcribe with Whisper
model = whisperx.load_model("large-v3-turbo", device, compute_type=compute_type)
result = model.transcribe(audio, batch_size=16)

# 3. Align transcription for word-level timestamps
model_a, metadata = whisperx.load_align_model(
    language_code=result["language"],
    device=device
)
result = whisperx.align(
    result["segments"],
    model_a,
    metadata,
    audio,
    device,
    return_char_alignments=False,
)

# 4. Run diarization
diarize_model = whisperx.DiarizationPipeline(
    use_auth_token=hf_token,
    device=device
)
diarize_segments = diarize_model(audio)

# 5. Assign speakers to words
result = whisperx.assign_word_speakers(diarize_segments, result)

# 6. Output with speaker labels
for segment in result["segments"]:
    speaker = segment.get("speaker", "UNKNOWN")
    print(f"[{speaker}] {segment['text']}")
```

### Specifying Number of Speakers

```python
# If you know the number of speakers
diarize_segments = diarize_model(
    audio,
    min_speakers=2,
    max_speakers=2,
)

# Or let it auto-detect
diarize_segments = diarize_model(audio)
```

## Output Format

### Segment with Speaker Labels

```python
{
    "start": 0.0,
    "end": 2.5,
    "text": "Hello, welcome to the meeting.",
    "speaker": "SPEAKER_00",
    "words": [
        {"word": "Hello,", "start": 0.0, "end": 0.5, "speaker": "SPEAKER_00"},
        {"word": "welcome", "start": 0.6, "end": 1.0, "speaker": "SPEAKER_00"},
        ...
    ]
}
```

### Formatting Output

```python
def format_transcript_with_speakers(result):
    """Format transcript with speaker labels."""
    output_lines = []
    current_speaker = None

    for segment in result["segments"]:
        speaker = segment.get("speaker", "UNKNOWN")

        # Only add speaker label when it changes
        if speaker != current_speaker:
            current_speaker = speaker
            output_lines.append(f"\n[{speaker}]")

        output_lines.append(segment["text"].strip())

    return " ".join(output_lines).strip()
```

## pyannote Directly (Alternative)

For more control, use pyannote.audio directly:

```python
from pyannote.audio import Pipeline
import torch

# Initialize pipeline
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="your_hf_token"
)

# Send to GPU if available
if torch.cuda.is_available():
    pipeline.to(torch.device("cuda"))

# Run diarization
diarization = pipeline("audio.wav")

# Iterate over speaker turns
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"Speaker {speaker}: {turn.start:.2f}s - {turn.end:.2f}s")
```

## Memory Considerations

### GPU Memory for Diarization

| Component              | Approximate VRAM |
| ---------------------- | ---------------- |
| Whisper large-v3-turbo | ~6GB             |
| Alignment model        | ~1GB             |
| Diarization model      | ~2GB             |
| **Total**              | **~9GB**         |

### Reducing Memory Usage

```python
# Process in stages, unloading models between steps
import gc
import torch

# After transcription
del model
gc.collect()
torch.cuda.empty_cache()

# Load alignment model
model_a, metadata = whisperx.load_align_model(...)
result = whisperx.align(...)

# Unload alignment model
del model_a
gc.collect()
torch.cuda.empty_cache()

# Load diarization model
diarize_model = whisperx.DiarizationPipeline(...)
```

## Limitations

1. **HuggingFace Token Required** - Must accept model terms
2. **GPU Recommended** - CPU inference is slow for diarization
3. **Memory Intensive** - Full pipeline needs ~9GB VRAM
4. **Not Perfect** - May misattribute speakers at boundaries
5. **Short Segments** - Very short utterances may be misclassified

## Best Practices

1. **Use longer audio** - Diarization works better with more context
2. **Specify speaker count** - If known, improves accuracy
3. **Clean audio** - Background noise affects speaker separation
4. **Stereo separation** - If speakers are on different channels, process separately

## Sources

- [WhisperX GitHub](https://github.com/m-bain/whisperX)
- [pyannote.audio Documentation](https://github.com/pyannote/pyannote-audio)
- [pyannote Speaker Diarization](https://huggingface.co/pyannote/speaker-diarization-3.1)

## Related Documents

- [ADR-002: Diarization](../architecture/adr/002-diarization.md) - Decision to use
  WhisperX for diarization
- [Feature: Diarization](../feature/diarization.md) - User-facing diarization
  documentation
- [Component: Transcription Engine](../architecture/components/transcription-engine.md) -
  Implementation details
