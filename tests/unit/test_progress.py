"""Tests for progress utilities."""

from __future__ import annotations

import sys
from unittest.mock import patch

from scribbulus.utils.progress import (
    ProgressConfig,
    create_stage_callback,
    progress_context,
    progress_iterator,
)


class TestProgressConfig:
    """Test ProgressConfig class."""

    def test_default_values(self):
        """Default config should have progress enabled."""
        config = ProgressConfig()
        assert config.enabled is True
        assert config.verbose is False

    def test_disabled_by_ci_env(self):
        """Progress should be disabled when CI=true."""
        with (
            patch.dict("os.environ", {"CI": "true"}, clear=True),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is False

    def test_disabled_by_ci_env_value_1(self):
        """Progress should be disabled when CI=1."""
        with (
            patch.dict("os.environ", {"CI": "1"}, clear=True),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is False

    def test_disabled_by_explicit_env(self):
        """Progress should be disabled when SCRIBBULUS_NO_PROGRESS=1."""
        with (
            patch.dict(
                "os.environ", {"SCRIBBULUS_NO_PROGRESS": "1"}, clear=True
            ),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is False

    def test_disabled_by_explicit_env_true(self):
        """Progress should be disabled when SCRIBBULUS_NO_PROGRESS=true."""
        with (
            patch.dict(
                "os.environ", {"SCRIBBULUS_NO_PROGRESS": "true"}, clear=True
            ),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is False

    def test_disabled_by_explicit_env_yes(self):
        """Progress should be disabled when SCRIBBULUS_NO_PROGRESS=yes."""
        with (
            patch.dict(
                "os.environ", {"SCRIBBULUS_NO_PROGRESS": "yes"}, clear=True
            ),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is False

    def test_disabled_when_not_tty(self):
        """Progress should be disabled when stderr is not a TTY."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(sys.stderr, "isatty", return_value=False),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is False

    def test_enabled_in_tty_without_env(self):
        """Progress should be enabled in TTY without disabling env vars."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment()
            assert config.enabled is True

    def test_verbose_passed_through(self):
        """Verbose flag should be passed through."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(sys.stderr, "isatty", return_value=True),
        ):
            config = ProgressConfig.from_environment(verbose=True)
            assert config.verbose is True


class TestProgressIterator:
    """Test progress_iterator function."""

    def test_iterates_all_items(self):
        """Should iterate through all items."""
        items = [1, 2, 3, 4, 5]
        result = list(progress_iterator(items, disable=True))
        assert result == items

    def test_handles_empty_iterable(self):
        """Should handle empty iterables."""
        items: list[int] = []
        result = list(progress_iterator(items, disable=True))
        assert result == []

    def test_disabled_produces_no_output(self, capsys):
        """Disabled progress should produce no stderr output."""
        items = [1, 2, 3]
        list(progress_iterator(items, disable=True))
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_respects_total_parameter(self):
        """Should accept total parameter."""
        items = iter([1, 2, 3])
        # Should not raise with total parameter
        result = list(progress_iterator(items, total=3, disable=True))
        assert result == [1, 2, 3]

    def test_respects_desc_parameter(self):
        """Should accept desc parameter."""
        items = [1, 2, 3]
        # Should not raise with desc parameter
        result = list(
            progress_iterator(items, desc="Processing", disable=True)
        )
        assert result == [1, 2, 3]


class TestProgressContext:
    """Test progress_context context manager."""

    def test_yields_progress_bar(self):
        """Should yield a progress bar with update method."""
        with progress_context(total=10, disable=True) as pbar:
            assert hasattr(pbar, "update")
            assert hasattr(pbar, "n")

    def test_update_increments_progress(self):
        """Update should increment progress counter when enabled."""
        # Test with disable=False to verify counter increments
        # Output goes to stderr which we can capture
        with progress_context(total=10, disable=False) as pbar:
            assert pbar.n == 0
            pbar.update(1)
            assert pbar.n == 1
            pbar.update(5)
            assert pbar.n == 6

    def test_update_callable_when_disabled(self):
        """Update should be callable without error when disabled."""
        with progress_context(total=10, disable=True) as pbar:
            # When disabled, tqdm doesn't track updates (by design)
            # but the method should still be callable
            pbar.update(1)
            pbar.update(5)

    def test_disabled_produces_no_output(self, capsys):
        """Disabled progress should produce no stderr output."""
        with progress_context(total=10, disable=True) as pbar:
            pbar.update(5)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_closes_on_exit(self):
        """Progress bar should be closed on context exit."""
        with progress_context(total=10, disable=True) as pbar:
            pass
        # After context exit, disable should be set (tqdm internal state)
        assert pbar.disable is True


class TestCreateStageCallback:
    """Test create_stage_callback function."""

    def test_returns_callable(self):
        """Should return a callable."""
        callback = create_stage_callback(disable=True)
        assert callable(callback)

    def test_accepts_stage_and_progress(self):
        """Callback should accept stage name and progress float."""
        callback = create_stage_callback(disable=True)
        # Should not raise
        callback("Test Stage", 0.5)

    def test_handles_progress_completion(self):
        """Callback should handle progress reaching 1.0."""
        callback = create_stage_callback(disable=True)
        # Should not raise
        callback("Test Stage", 0.0)
        callback("Test Stage", 0.5)
        callback("Test Stage", 1.0)

    def test_handles_stage_transitions(self):
        """Callback should handle transitions between stages."""
        callback = create_stage_callback(disable=True)
        # Should not raise
        callback("Stage 1", 0.0)
        callback("Stage 1", 1.0)
        callback("Stage 2", 0.0)
        callback("Stage 2", 1.0)

    def test_handles_rapid_updates(self):
        """Callback should handle rapid progress updates."""
        callback = create_stage_callback(disable=True)
        for i in range(100):
            callback("Processing", i / 100)
        callback("Processing", 1.0)

    def test_disabled_produces_no_output(self, capsys):
        """Disabled callback should produce no stderr output."""
        callback = create_stage_callback(disable=True)
        callback("Test Stage", 0.0)
        callback("Test Stage", 0.5)
        callback("Test Stage", 1.0)
        captured = capsys.readouterr()
        assert captured.err == ""
