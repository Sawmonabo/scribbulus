---
task_id: transcribe-command-fixes
status: completed
created: 2025-12-28
updated: 2025-12-28
priority: high
depends_on: []
---

# Transcribe Command Fixes

## Summary

Fix four categories of failures affecting `scribbulus transcribe` command:
packaging/import resolution, TorIO FFmpeg extension loading, PyTorch safe
loading for diarization, and third-party DEBUG log noise.

## Problem Statement

Running `scribbulus transcribe` fails intermittently or produces noisy output.
Evidence from `console_error.txt`:

1. **ModuleNotFoundError** after successful install:

   ```text
   ModuleNotFoundError: No module named 'scribbulus'
   ```

   Occurs when running `uv run scribbulus ...` even after
   `uv pip install -e ".[all]"` succeeds.

2. **TorIO FFmpeg extension failures** on macOS:

   ```text
   OSError: dlopen(.../libtorio_ffmpeg6.so): Library not loaded:
     @rpath/libavutil.58.dylib
     Reason: no LC_RPATH's found
   ```

3. **Diarization fails** with PyTorch 2.6+ safe loading:

   ```text
   WeightsUnpickler error: Unsupported global:
     GLOBAL torch.torch_version.TorchVersion
   ```

4. **DEBUG log spam** from third-party libraries:
   matplotlib, urllib3, torio, filelock, speechbrain, fsspec

## Goals

1. Make `scribbulus transcribe` work reliably from a clean install
2. Ensure diarization works with HF_TOKEN set
3. Produce clean output at default verbosity (no DEBUG spam)
4. Provide actionable error messages and diagnostic tools

## Non-Goals

- Major architecture changes to transcription pipeline
- Upgrading to pyannote-audio 4.x (requires whisperx update)
- Supporting Python < 3.13

## Design Decisions

| Decision | Choice | Rationale |
| -------- | ------ | --------- |
| Package discovery | `packages = ["src/scribbulus"]` + `dev-mode-dirs = ["src"]` | Fixed Hatchling editable install |
| Audio backend location | `transcription/audio_backend.py` | Belongs with transcription code, not utils |
| Audio backend | soundfile (required dep) | Portable, avoids TorIO FFmpeg RPATH issues |
| PyTorch safe loading | `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` env var | Community-recommended workaround |
| Logging module | `utils/logging.py` with RichHandler | Centralized, pretty output |
| App initialization | Audio backend config in `cli/main.py` | Single entry point, no import-time side effects |

## Implementation Steps

1. Create documentation (plan and state files)
2. Create research docs (pytorch-safe-loading.md, torchaudio-backends.md)
3. Fix `pyproject.toml` Hatchling package discovery and editable install
4. Create `src/scribbulus/utils/logging.py` with RichHandler
5. Create `src/scribbulus/transcription/audio_backend.py`
6. Update `cli/main.py` with centralized initialization
7. Update `cli/transcribe.py` to use logging module
8. Clean up `transcription/diarization.py` imports
9. Update `scripts/install.sh` with validation step
10. Update `scripts/install-ffmpeg.sh` with libsndfile installation
11. Create `scripts/doctor.sh` diagnostic command
12. Create tests for audio_backend module
13. Run verification (make lint, pytest)

## Files Changed

| File | Change |
| ---- | ------ |
| `pyproject.toml` | Fixed hatch editable install, added rich dep |
| `src/scribbulus/utils/logging.py` | NEW - Centralized logging with RichHandler |
| `src/scribbulus/transcription/audio_backend.py` | NEW - torchaudio backend config |
| `src/scribbulus/cli/main.py` | Added audio backend initialization |
| `src/scribbulus/cli/transcribe.py` | Removed logging setup, imports from utils |
| `src/scribbulus/transcription/diarization.py` | Cleaned imports, removed isort hacks |
| `src/scribbulus/utils/__init__.py` | Added exports for logging functions |
| `scripts/install.sh` | Added validation step |
| `scripts/install-ffmpeg.sh` | Added libsndfile installation |
| `scripts/doctor.sh` | NEW - Diagnostic command |
| `tests/unit/test_audio_backend.py` | NEW - 10 tests for audio backend |

## Risks

| Risk | Likelihood | Impact | Mitigation |
| ---- | ---------- | ------ | ---------- |
| whisperx breaks with upstream changes | Low | High | Pin version, monitor releases |
| soundfile not available on some platforms | Low | Medium | Fall back to sox_io backend |
| Env var workaround stops working | Low | Medium | Monitor PyTorch releases |
| torchaudio backend API deprecated | High | Low | Warnings suppressed, will migrate to TorchCodec |

## Related Documents

- [Research: PyTorch Safe Loading](../research/pytorch-safe-loading.md)
- [Research: TorchAudio Backends](../research/torchaudio-backends.md)
