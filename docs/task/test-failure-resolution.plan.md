---
task_id: test-failure-resolution
status: completed
created: 2025-12-19
updated: 2025-12-19
priority: high
depends_on: []
---

# Test Failure Resolution

## Summary

Fix four failing tests related to chunking pipeline configuration and audio
duration calculation for silent files.

## Problem Statement

Four tests were failing after recent changes:

1. `test_chunking_pipeline` - Test bug passing `temp_dir` to wrong constructor
2. `test_transcribe_silent_audio` - Duration calculated as 0.0 for silent audio
3. `test_transcribe_video_file` - Same duration calculation bug
4. `test_transcribe_file_basic` - Same duration calculation bug

## Goals

1. Fix all four failing tests
2. Ensure no new test failures are introduced
3. Address root causes, not just symptoms

## Non-Goals

- Refactoring unrelated code
- Adding new test coverage beyond fixes

## Design Decisions

| Decision          | Choice                      | Rationale                                               |
| ----------------- | --------------------------- | ------------------------------------------------------- |
| Duration source   | Use `info.duration`         | Returns actual audio length even for silent files       |
| Test fix approach | Correct parameter placement | `temp_dir` belongs to AudioChunker, not ChunkingConfig  |

## Implementation Steps

1. Fix `test_chunking_pipeline` - Move `temp_dir` parameter to AudioChunker
2. Fix duration calculation in `whisper_backend.py` - Use `info.duration`
3. Run full test suite to verify fixes

## Risks

| Risk                      | Likelihood | Impact | Mitigation                            |
| ------------------------- | ---------- | ------ | ------------------------------------- |
| Fix causes other failures | Low        | High   | Run full test suite after each change |

## Related Documents

- [Architecture: Transcription Engine](../architecture/components/transcription-engine.md)
