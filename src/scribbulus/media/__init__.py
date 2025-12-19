"""Media handling module for scribbulus."""

from scribbulus.media.formats import (
    SUPPORTED_AUDIO,
    SUPPORTED_VIDEO,
    MediaInfo,
    get_file_type,
    is_supported,
)

__all__ = [
    "SUPPORTED_AUDIO",
    "SUPPORTED_VIDEO",
    "MediaInfo",
    "get_file_type",
    "is_supported",
]
