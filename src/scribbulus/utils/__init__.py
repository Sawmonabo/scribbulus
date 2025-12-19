"""Utilities module for scribbulus."""

from scribbulus.utils.errors import ScribbulusError
from scribbulus.utils.formatter import (
    DEFAULT_LINE_WIDTH,
    FormatterConfig,
    format_diarized_segments,
    format_simple_segments,
    format_time,
    wrap_text,
)
from scribbulus.utils.progress import (
    ProgressCallback,
    ProgressConfig,
    create_stage_callback,
    progress_context,
    progress_iterator,
)

__all__ = [
    "DEFAULT_LINE_WIDTH",
    "FormatterConfig",
    "ProgressCallback",
    "ProgressConfig",
    "ScribbulusError",
    "create_stage_callback",
    "format_diarized_segments",
    "format_simple_segments",
    "format_time",
    "progress_context",
    "progress_iterator",
    "wrap_text",
]
