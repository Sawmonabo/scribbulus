"""Centralized dependency management and device detection utilities.

This module provides reusable utilities for:
- Checking availability of optional and required dependencies
- Resolving compute devices (CPU/GPU)
- Cleaning up GPU memory
- Consistent error messages for missing dependencies

Design Principles:
- Required dependencies (torch, faster-whisper) are declared in pyproject.toml
  and should be present. Availability checks exist for graceful degradation
  and clear error messaging.
- Optional dependencies (whisperx) are extras and may not be installed.
  Feature code should check availability before use.
- Device detection is cached to avoid repeated probing.
- All import mechanics are centralized here to keep business logic clean.
"""

from __future__ import annotations

import gc
import importlib.util
from functools import lru_cache
from typing import TYPE_CHECKING

from scribbulus.utils.errors import DiarizationError, ModelNotFoundError
from scribbulus.utils.types import DeviceType, ResolvedDeviceType

if TYPE_CHECKING:
    import types


# ---------------------------------------------------------------------------
# Error message templates for consistent user guidance
# ---------------------------------------------------------------------------

TORCH_IMPORT_ERROR = (
    "PyTorch is not installed but is required. "
    "Run: pip install torch torchaudio"
)

FASTER_WHISPER_IMPORT_ERROR = (
    "faster-whisper is not installed but is required. "
    "Run: pip install faster-whisper"
)

WHISPERX_IMPORT_ERROR = (
    "whisperx is not installed. This is an optional dependency for "
    "speaker diarization. "
    "Run: pip install scribbulus[diarization] or pip install whisperx"
)


# ---------------------------------------------------------------------------
# Package availability checks (cached)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def is_torch_available() -> bool:
    """
    Check if PyTorch is installed.

    :returns: True if torch can be imported, False otherwise.
    """
    return importlib.util.find_spec("torch") is not None


@lru_cache(maxsize=1)
def is_faster_whisper_available() -> bool:
    """
    Check if faster-whisper is installed.

    :returns: True if faster_whisper can be imported, False otherwise.
    """
    return importlib.util.find_spec("faster_whisper") is not None


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

    Requires PyTorch to be installed. Returns False if PyTorch is not
    available or CUDA is not configured.

    :returns: True if CUDA is available, False otherwise.
    """
    if not is_torch_available():
        return False
    import torch

    return bool(torch.cuda.is_available())


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
    Clean up GPU memory if PyTorch/CUDA is available.

    Triggers Python garbage collection and clears the CUDA memory cache.
    Safe to call even if PyTorch is not installed or CUDA is not available.
    """
    gc.collect()
    if is_cuda_available():
        import torch

        torch.cuda.empty_cache()


# ---------------------------------------------------------------------------
# Dependency requirement assertions
# ---------------------------------------------------------------------------


def require_torch() -> None:
    """
    Assert that PyTorch is available, raising a helpful error if not.

    :raises ModelNotFoundError: If PyTorch is not installed.
    """
    if not is_torch_available():
        raise ModelNotFoundError("torch", TORCH_IMPORT_ERROR)


def require_faster_whisper() -> None:
    """
    Assert that faster-whisper is available, raising a helpful error if not.

    :raises ModelNotFoundError: If faster-whisper is not installed.
    """
    if not is_faster_whisper_available():
        raise ModelNotFoundError("faster-whisper", FASTER_WHISPER_IMPORT_ERROR)


def require_whisperx() -> None:
    """
    Assert that whisperx is available, raising a helpful error if not.

    whisperx is an optional dependency for speaker diarization.

    :raises DiarizationError: If whisperx is not installed.
    """
    if not is_whisperx_available():
        raise DiarizationError(WHISPERX_IMPORT_ERROR)


# ---------------------------------------------------------------------------
# Module getters for optional dependencies
# ---------------------------------------------------------------------------


def get_whisperx() -> types.ModuleType:
    """
    Get the whisperx module, raising a helpful error if not installed.

    :returns: The whisperx module.
    :raises DiarizationError: If whisperx is not installed.
    """
    require_whisperx()
    import whisperx

    return whisperx  # type: ignore[no-any-return]


def get_faster_whisper_model() -> type:
    """
    Get the WhisperModel class from faster-whisper.

    :returns: The WhisperModel class.
    :raises ModelNotFoundError: If faster-whisper is not installed.
    """
    require_faster_whisper()
    from faster_whisper import WhisperModel

    return WhisperModel  # type: ignore[no-any-return]
