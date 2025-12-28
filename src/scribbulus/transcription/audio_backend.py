"""Configure torchaudio backend for cross-platform compatibility.

This module configures torchaudio to use the soundfile backend instead of
the default FFmpeg backend. This avoids TorIO FFmpeg extension loading issues
on macOS where the FFmpeg dylibs may not be discoverable via RPATH.

The soundfile backend uses libsndfile which is more portable and doesn't
have the RPATH issues that TorIO's FFmpeg extension has.

See: docs/research/torchaudio-backends.md
"""

from __future__ import annotations

import logging
import os
import warnings

import torchaudio  # Top-level import - required dependency

logger = logging.getLogger(__name__)

_backend_configured = False


def configure_audio_backend() -> None:
    """
    Configure torchaudio to use soundfile backend.

    This function should be called early at app startup before any code that
    might trigger torchaudio imports. It's safe to call multiple times -
    only the first call has any effect.

    The function:
    1. Sets TORCHAUDIO_USE_BACKEND_DISPATCHER env var
    2. Sets the backend to soundfile (preferred) or sox_io (fallback)
    """
    global _backend_configured  # noqa: PLW0603

    if _backend_configured:
        return

    # Set environment variable before any backend operations
    os.environ.setdefault("TORCHAUDIO_USE_BACKEND_DISPATCHER", "1")

    # Suppress torchaudio deprecation warnings (transitioning to TorchCodec)
    # These APIs are deprecated but still functional in torchaudio 2.8.x
    warnings.filterwarnings(
        "ignore",
        message=r"torchaudio\._backend\.(list_audio_backends|set_audio_backend)",
        category=UserWarning,
    )

    # Get available backends
    try:
        backends = torchaudio.list_audio_backends()
    except Exception:
        backends = []

    # Try to set soundfile as preferred backend
    if "soundfile" in backends:
        try:
            torchaudio.set_audio_backend("soundfile")
            logger.debug("Configured torchaudio to use soundfile backend")
            _backend_configured = True
            return
        except Exception as e:
            logger.debug(f"Failed to set soundfile backend: {e}")

    # Fall back to sox_io
    if "sox_io" in backends:
        try:
            torchaudio.set_audio_backend("sox_io")
            logger.debug("Configured torchaudio to use sox_io backend")
            _backend_configured = True
            return
        except Exception as e:
            logger.debug(f"Failed to set sox_io backend: {e}")

    # If no portable backend is available, log a warning
    if backends:
        logger.debug(f"Available backends: {backends}")
    else:
        logger.debug("Could not determine available torchaudio backends")

    logger.warning(
        "No portable torchaudio audio backend available (soundfile, sox_io). "
        "Diarization may fail on some platforms due to FFmpeg extension issues. "
        "Install soundfile: pip install soundfile"
    )

    _backend_configured = True
