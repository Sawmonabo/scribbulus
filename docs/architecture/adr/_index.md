---
last_updated: 2025-12-20T00:30:00Z
---

# Architecture Decision Records

## Overview

This directory contains Architecture Decision Records (ADRs) documenting
significant technical decisions made in this project. ADRs capture the context,
decision, and consequences of architectural choices.

## Active Decisions

| ADR                              | Title                                   | Status   | Date       |
| -------------------------------- | --------------------------------------- | -------- | ---------- |
| [001](./001-whisper-engine.md)   | Use faster-whisper for transcription    | accepted | 2025-12-14 |
| [002](./002-diarization.md)      | Use WhisperX for speaker diarization    | accepted | 2025-12-14 |

## Deprecated/Superseded

(none)

## How to Add an ADR

1. Copy `_template.md` to `NNN-{slug}.md` (next sequential number)
2. Fill in context, decision, and consequences
3. Link to relevant research docs
4. Update this index
5. Submit PR for review

## ADR Format

Each ADR follows the format:

- **Status**: proposed, accepted, deprecated, or superseded
- **Context**: What problem are we solving?
- **Decision**: What did we decide?
- **Consequences**: What are the positive, negative, and neutral outcomes?
- **Research References**: Links to research that informed the decision

## Related Documents

- [Architecture Overview](../overview.md)
- [Research](../../research/)
