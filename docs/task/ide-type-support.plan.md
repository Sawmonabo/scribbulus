---
task_id: ide-type-support
status: completed
created: 2025-12-19
updated: 2025-12-19
priority: medium
depends_on: []
---

# IDE Type Support

## Summary

Add Protocol-based type definitions to enable IDE autocomplete and type checking
for optional dependencies (faster-whisper, whisperx) without requiring them to
be installed.

## Problem Statement

The codebase uses optional dependencies (faster-whisper, whisperx) that may not
be installed in development environments. Without proper type hints, IDEs cannot
provide autocomplete or type checking for code that interacts with these
libraries, reducing developer productivity and increasing the risk of runtime
errors.

## Goals

1. Enable IDE autocomplete for faster-whisper and whisperx APIs
2. Support mypy type checking without requiring libraries to be installed
3. Maintain runtime compatibility with actual library types

## Non-Goals

- Runtime type validation (Protocols are structural, not runtime checks)
- Complete type coverage for all library internals

## Design Decisions

| Decision       | Choice                     | Rationale                                         |
| -------------- | -------------------------- | ------------------------------------------------- |
| Type approach  | Protocol classes           | Works without libs installed, provides IDE support|
| Coverage scope | Public API methods         | Full coverage for commonly used methods           |
| Return types   | Use `Any` for complex types| External lib types too complex to replicate       |

## Implementation Steps

1. Create `src/scribbulus/utils/types.py` - Protocol definitions
2. Update `src/scribbulus/utils/deps.py` - Change return types to use Protocols
3. Update `whisper_backend.py` - Add type hints to `_model`
4. Update `diarization.py` - Add type hints to `_diarize_model`
5. Run quality checks - Ensure lint and typecheck pass

## Risks

| Risk                           | Likelihood | Impact | Mitigation                                |
| ------------------------------ | ---------- | ------ | ----------------------------------------- |
| Protocol drift from actual API | Low        | Medium | Document which lib versions are targeted  |
| Incomplete type coverage       | Medium     | Low    | Focus on commonly used methods first      |

## Related Documents

- [Feature: Transcription](../feature/transcription.md) - Transcription feature docs
- [Feature: Diarization](../feature/diarization.md) - Diarization feature docs
