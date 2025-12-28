---
updated: 2025-12-28
---

# Scribbulus Documentation

## Quick Links

| Need to...                  | Go to...                                           |
| --------------------------- | -------------------------------------------------- |
| Use a feature               | [Feature Docs](./feature/)                         |
| Understand the architecture | [Architecture Overview](./architecture/overview.md)|
| See why a decision was made | [ADRs](./architecture/adr/_index.md)               |
| Read technical research     | [Research](./research/)                            |
| Track active work           | [Task Index](./task/_index.md)                     |

## Documentation Modules

### [Feature Documentation](./feature/)

User-facing documentation for each feature.

- [Transcription](./feature/transcription.md) - Core speech-to-text
- [Diarization](./feature/diarization.md) - Speaker identification
- [Output Formats](./feature/output-formats.md) - Output formatting options

### [Architecture](./architecture/)

System design and technical decisions.

- [Overview](./architecture/overview.md) - System architecture
- [ADRs](./architecture/adr/_index.md) - Architectural decisions
- [Components](./architecture/components/) - Component deep-dives
  - [Transcription Engine](./architecture/components/transcription-engine.md)
  - [Media Processor](./architecture/components/media-processor.md)

### [Research](./research/)

Technical research and analysis.

- [Whisper Models](./research/whisper-models.md) - Model comparison
- [Speech-to-Text Options](./research/speech-to-text-options.md) - STT comparison
- [Diarization Guide](./research/diarization-guide.md) - Speaker diarization
- [FFmpeg Audio Extraction](./research/ffmpeg-audio-extraction.md) - Audio extraction
- [PyTorch Safe Loading](./research/pytorch-safe-loading.md) - weights_only compatibility
- [TorchAudio Backends](./research/torchaudio-backends.md) - Audio backend selection

### [Task Tracking](./task/)

Active work plans and state.

- [Active Tasks Index](./task/_index.md)

## For AI Agents

Each module contains `_template.md` files for creating new documentation:

| Module                     | Template              | Purpose           |
| -------------------------- | --------------------- | ----------------- |
| `feature/`                 | `_template.md`        | New feature docs  |
| `architecture/`            | `_template.md`        | Architecture docs |
| `architecture/adr/`        | `_template.md`        | New ADRs          |
| `architecture/components/` | `_template.md`        | Component docs    |
| `research/`                | `_template.md`        | Research docs     |
| `task/`                    | `_template.plan.md`   | Task plans        |
| `task/`                    | `_template.state.md`  | Task state        |

### Creating New Documentation

1. Find the appropriate module for your documentation
2. Read the `_template.md` file in that module
3. Copy the template structure to a new file
4. Fill in all sections
5. Add cross-references to related docs
6. Ensure links use relative paths

## Contributing

### Documentation Standards

- Use [CommonMark](https://commonmark.org/) markdown
- Keep line length under 80 characters in prose
- Use YAML frontmatter for metadata
- Include "Related Documents" section in all docs
- Link, don't duplicate content

### Review Process

- Feature docs: Reviewed with feature PRs
- Architecture/ADRs: Team review before implementation
- Research: Self-service, update as needed
- Task state: Self-service, no review required
