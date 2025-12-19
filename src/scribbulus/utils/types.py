"""Centralized type definitions for scribbulus.

This module contains reusable type aliases that are shared across
multiple modules. Domain-specific types that are only used within
a single module should remain in that module.
"""

from __future__ import annotations

from typing import Literal

# Device types for compute operations
DeviceType = Literal["cuda", "cpu", "auto"]
"""User-facing device selection including auto-detection."""

ResolvedDeviceType = Literal["cuda", "cpu"]
"""Resolved device type after auto-detection (no 'auto')."""

# Whisper model configuration types
ModelSize = Literal[
    "tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"
]
"""Available Whisper model sizes."""

ComputeType = Literal["float16", "int8_float16", "int8", "float32"]
"""Compute precision types for inference."""
