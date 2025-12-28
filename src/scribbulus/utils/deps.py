"""Centralized dependency management and device detection utilities.

Dependency Model
================

REQUIRED DEPENDENCIES (always available after install):
    torch          - ML inference, GPU detection, memory cleanup
    faster-whisper - CTranslate2-optimized Whisper transcription
    click          - CLI framework
    tqdm           - Progress bars
    pydub          - Audio manipulation (planned for future features)
    torchaudio     - Audio processing (planned for future features)

OPTIONAL DEPENDENCIES (extras):
    whisperx [diarization] - Speaker diarization
        Install: pip install scribbulus[diarization]
        Check: is_whisperx_available()
        Import: get_whisperx()

EXTERNAL TOOLS:
    ffmpeg/ffprobe - Required for audio/video processing

Design Principles
=================
- Required deps are imported directly (guaranteed by pip/uv)
- Optional deps use lazy imports with availability checks
- Device detection cached for efficiency
"""

from __future__ import annotations

import gc
import importlib.util
from functools import lru_cache
from typing import TYPE_CHECKING, cast

import torch

from scribbulus.utils.errors import DiarizationError
from scribbulus.utils.types import (
    DeviceType,
    ResolvedDeviceType,
    WhisperXModuleProtocol,
)

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Error message templates for optional dependencies
# ---------------------------------------------------------------------------

WHISPERX_IMPORT_ERROR = (
    "whisperx is not installed. This is an optional dependency for "
    "speaker diarization. "
    "Run: pip install scribbulus[diarization] or pip install whisperx"
)


# ---------------------------------------------------------------------------
# Optional dependency availability check (cached)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def is_whisperx_available() -> bool:
    """
    Check if whisperx is installed (optional dependency).

    :returns: True if whisperx can be imported, False otherwise.
    """
    return importlib.util.find_spec("whisperx") is not None


@lru_cache(maxsize=1)
def is_cuda_available() -> bool:
    """
    Check if CUDA is available for GPU acceleration.

    :returns: True if CUDA is available, False otherwise.
    """
    return torch.cuda.is_available()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Device detection and resolution
# ---------------------------------------------------------------------------


def get_device(preferred: DeviceType = "auto") -> ResolvedDeviceType:
    """
    Determine the compute device to use.

    :param preferred: Preferred device - "auto", "cuda", or "cpu".
                     "auto" will use CUDA if available, else CPU.
    :returns: The resolved device type ("cuda" or "cpu").
    """
    if preferred == "cuda":
        return "cuda"
    if preferred == "cpu":
        return "cpu"
    # Auto-detect: prefer CUDA if available
    return "cuda" if is_cuda_available() else "cpu"


# ---------------------------------------------------------------------------
# Resource cleanup utilities
# ---------------------------------------------------------------------------


def cleanup_gpu_memory() -> None:
    """
    Clean up GPU memory.

    Triggers Python garbage collection and clears the CUDA memory cache
    if CUDA is available.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ---------------------------------------------------------------------------
# Dependency requirement assertion (optional deps only)
# ---------------------------------------------------------------------------


def require_whisperx() -> None:
    """
    Assert that whisperx is available, raising a helpful error if not.

    whisperx is an optional dependency for speaker diarization.

    :raises DiarizationError: If whisperx is not installed.
    """
    if not is_whisperx_available():
        raise DiarizationError(WHISPERX_IMPORT_ERROR)


# ---------------------------------------------------------------------------
# Module getters
# ---------------------------------------------------------------------------


def get_whisperx() -> WhisperXModuleProtocol:
    """
    Get the whisperx module, raising a helpful error if not installed.

    :returns: The whisperx module.
    :raises DiarizationError: If whisperx is not installed.
    """
    require_whisperx()
    import whisperx  # pyright: ignore[reportMissingImports]

    return cast(WhisperXModuleProtocol, whisperx)


def get_diarization_pipeline() -> type:
    """
    Get the DiarizationPipeline class from whisperx.diarize submodule.

    Note: DiarizationPipeline is not exported at the whisperx module level,
    it must be imported from the whisperx.diarize submodule directly.

    :returns: The DiarizationPipeline class.
    :raises DiarizationError: If whisperx is not installed.
    """
    require_whisperx()
    from whisperx.diarize import (
        DiarizationPipeline,  # pyright: ignore[reportMissingImports]
    )

    return DiarizationPipeline  # type: ignore[no-any-return]
