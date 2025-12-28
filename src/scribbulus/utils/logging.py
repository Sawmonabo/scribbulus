"""Logging configuration for scribbulus."""

from __future__ import annotations

import logging
import warnings

from rich.console import Console
from rich.logging import RichHandler

# Third-party loggers to silence unless verbose mode is enabled
_NOISY_LOGGERS = [
    "matplotlib",
    "matplotlib.font_manager",
    "urllib3",
    "urllib3.connectionpool",
    "torio",
    "torio._extension",
    "torio._extension.utils",
    "filelock",
    "speechbrain",
    "speechbrain.utils",
    "speechbrain.utils.checkpoints",
    "speechbrain.utils.quirks",
    "fsspec",
    "fsspec.local",
    "huggingface_hub",
]

# Module-level console for reuse
_console: Console | None = None


def get_console() -> Console:
    """Get the shared rich console instance."""
    global _console  # noqa: PLW0603 - module-level singleton pattern
    if _console is None:
        _console = Console(stderr=True)
    return _console


def setup_logging(verbose: bool) -> None:
    """
    Configure logging with rich handler.

    At default verbosity (not verbose):
    - Application logs at WARNING level
    - Third-party libraries silenced to WARNING/ERROR

    At verbose (-v):
    - Application logs at DEBUG level
    - Third-party libraries at INFO level (not DEBUG to avoid noise)

    :param verbose: Enable debug-level logging if True, warning-level if False.
    """
    # Suppress pyannote SyntaxWarnings for unescaped regex strings
    warnings.filterwarnings(
        "ignore",
        message=r"invalid escape sequence",
        category=SyntaxWarning,
        module=r"pyannote\..*",
    )

    app_level = logging.DEBUG if verbose else logging.WARNING

    # Use RichHandler for pretty logs
    logging.basicConfig(
        level=app_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=get_console(),
                show_time=verbose,
                show_path=verbose,
                rich_tracebacks=True,
            )
        ],
    )

    # Configure application logger
    logging.getLogger("scribbulus").setLevel(app_level)

    # Silence noisy third-party loggers
    third_party_level = logging.INFO if verbose else logging.WARNING
    for logger_name in _NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(third_party_level)

    # faster-whisper at INFO even in verbose mode (DEBUG is too chatty)
    logging.getLogger("faster_whisper").setLevel(logging.INFO)
