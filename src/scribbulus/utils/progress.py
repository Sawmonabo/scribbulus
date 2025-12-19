"""Progress reporting utilities with CI-friendly fallbacks."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TypeVar

from tqdm import tqdm

T = TypeVar("T")

# Progress callback type (matches existing signature in TranscriptionEngine)
ProgressCallback = Callable[[str, float], None]


@dataclass
class ProgressConfig:
    """Configuration for progress display."""

    enabled: bool = True
    verbose: bool = False

    @classmethod
    def from_environment(cls, verbose: bool = False) -> ProgressConfig:
        """
        Create config based on environment detection.

        :param verbose: Enable verbose mode.
        :returns: ProgressConfig with appropriate settings.
        """
        # Respect SCRIBBULUS_NO_PROGRESS or CI environment
        disabled_by_env = os.getenv("SCRIBBULUS_NO_PROGRESS", "").lower() in (
            "1",
            "true",
            "yes",
        ) or os.getenv("CI", "").lower() in (
            "1",
            "true",
        )
        # Also check if stderr is a TTY
        is_tty = sys.stderr.isatty()

        return cls(
            enabled=not disabled_by_env and is_tty,
            verbose=verbose,
        )


def progress_iterator[T](
    iterable: Iterable[T],
    total: int | None = None,
    desc: str = "",
    unit: str = "it",
    disable: bool | None = None,
) -> Iterator[T]:
    """
    Wrap an iterable with progress reporting.

    :param iterable: Items to iterate over.
    :param total: Total count (if known).
    :param desc: Description shown in progress bar.
    :param unit: Unit name for items.
    :param disable: True=off, False=on, None=auto-detect TTY.
    :returns: Iterator that reports progress.
    """
    return iter(
        tqdm(
            iterable,
            total=total,
            desc=desc,
            unit=unit,
            file=sys.stderr,
            disable=disable,
            leave=True,
            dynamic_ncols=True,
        )
    )


@contextmanager
def progress_context(
    total: int,
    desc: str = "",
    unit: str = "it",
    disable: bool | None = None,
):
    """
    Context manager for manual progress updates.

    :param total: Total count.
    :param desc: Description shown in progress bar.
    :param unit: Unit name.
    :param disable: True=off, False=on, None=auto-detect.
    :yields: tqdm instance with update() method.

    Example:
        with progress_context(100, desc="Processing") as pbar:
            for item in items:
                process(item)
                pbar.update(1)
    """
    pbar = tqdm(
        total=total,
        desc=desc,
        unit=unit,
        file=sys.stderr,
        disable=disable,
        leave=True,
        dynamic_ncols=True,
    )
    try:
        yield pbar
    finally:
        pbar.close()


def create_stage_callback(
    disable: bool | None = None,
) -> ProgressCallback:
    """
    Create a progress callback for stage-based progress.

    Compatible with existing TranscriptionEngine.progress_callback signature.

    :param disable: True=off, False=on, None=auto-detect TTY.
    :returns: Callback function(stage: str, progress: float).
    """
    current_bar: dict[str, tqdm | None] = {"bar": None}
    current_stage: dict[str, str | None] = {"name": None}

    def callback(stage: str, progress: float) -> None:
        # Stage changed - close old bar, start new one
        if stage != current_stage["name"]:
            if current_bar["bar"] is not None:
                current_bar["bar"].close()

            current_stage["name"] = stage
            current_bar["bar"] = tqdm(
                total=100,
                desc=stage,
                file=sys.stderr,
                disable=disable,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| [{elapsed}<{remaining}]",
                leave=True,
            )

        # Update progress
        if current_bar["bar"] is not None:
            new_n = int(progress * 100)
            current_bar["bar"].n = new_n
            current_bar["bar"].refresh()

            # Close on completion
            if progress >= 1.0:
                current_bar["bar"].close()
                current_bar["bar"] = None
                current_stage["name"] = None

    return callback


__all__ = [
    "ProgressCallback",
    "ProgressConfig",
    "create_stage_callback",
    "progress_context",
    "progress_iterator",
]
