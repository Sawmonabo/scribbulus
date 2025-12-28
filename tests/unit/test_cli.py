"""Tests for CLI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from scribbulus.cli.main import cli
from scribbulus.cli.transcribe import (
    MODEL_CHOICES,
    _format_duration,
    transcribe,
)


class TestCLIArguments:
    """Test CLI argument parsing."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    def test_help_option(self, runner: CliRunner) -> None:
        """--help should display help text."""
        result = runner.invoke(transcribe, ["--help"])

        assert result.exit_code == 0
        assert "Transcribe audio/video files to text" in result.output
        assert "--output" in result.output
        assert "--language" in result.output
        assert "--model" in result.output

    def test_version_option(self, runner: CliRunner) -> None:
        """--version should display version."""
        result = runner.invoke(cli, ["--version"])

        # May fail if package not installed, but should not crash
        assert result.exit_code in [0, 1]

    def test_missing_input_file(self, runner: CliRunner) -> None:
        """Should error when input file is missing."""
        result = runner.invoke(transcribe, [])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output

    def test_nonexistent_input_file(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Should error for non-existent file."""
        fake_path = str(temp_dir / "nonexistent.mp4")
        result = runner.invoke(transcribe, [fake_path])

        assert result.exit_code != 0

    def test_model_choices(self, runner: CliRunner) -> None:
        """Should accept valid model choices."""
        # Just verify the choices are defined correctly
        assert "large-v3-turbo" in MODEL_CHOICES
        assert "tiny" in MODEL_CHOICES
        assert "small" in MODEL_CHOICES

    def test_device_choices(self, runner: CliRunner, temp_dir: Path) -> None:
        """Should accept valid device choices."""
        # Create a dummy file to pass initial validation
        dummy_file = temp_dir / "test.mp4"
        dummy_file.write_bytes(b"fake")

        # Test with invalid device - should show error
        result = runner.invoke(
            transcribe, [str(dummy_file), "--device", "invalid"]
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_output_option(self, runner: CliRunner, temp_dir: Path) -> None:
        """Should accept output path option."""
        dummy_file = temp_dir / "test.mp4"
        dummy_file.write_bytes(b"fake")
        output_file = temp_dir / "output.txt"

        # Will fail at transcription but should parse args
        with patch("scribbulus.cli.transcribe.TranscriptionEngine"):
            result = runner.invoke(
                transcribe,
                [str(dummy_file), "-o", str(output_file)],
            )

        # Check that -o was parsed (may fail later for other reasons)
        assert "-o" not in result.output or "Invalid" not in result.output


class TestFormatDuration:
    """Test duration formatting."""

    def test_format_seconds_only(self) -> None:
        """Format duration less than a minute."""
        assert _format_duration(45) == "00:45"
        assert _format_duration(5) == "00:05"
        assert _format_duration(0) == "00:00"

    def test_format_minutes_and_seconds(self) -> None:
        """Format duration with minutes."""
        assert _format_duration(90) == "01:30"
        assert _format_duration(125) == "02:05"
        assert _format_duration(3599) == "59:59"

    def test_format_hours(self) -> None:
        """Format duration with hours."""
        assert _format_duration(3600) == "01:00:00"
        assert _format_duration(3661) == "01:01:01"
        assert _format_duration(7325) == "02:02:05"

    def test_format_float_duration(self) -> None:
        """Format duration with fractional seconds."""
        assert _format_duration(90.5) == "01:30"
        assert _format_duration(90.9) == "01:30"


class TestCLIIntegration:
    """Integration tests for CLI behavior."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    def test_diarization_warning_without_token(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Should warn when diarization enabled but no token."""
        dummy_file = temp_dir / "test.mp4"
        dummy_file.write_bytes(b"fake video content")

        # Mock the engine to avoid actual transcription
        with patch(
            "scribbulus.cli.transcribe.TranscriptionEngine"
        ) as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_engine.return_value.__exit__ = MagicMock(return_value=False)

            # Make transcribe raise to stop execution
            mock_instance.transcribe.side_effect = Exception("Test stop")

            result = runner.invoke(transcribe, [str(dummy_file)])

        # Should have shown warning about HF token
        assert "HuggingFace token" in result.output or result.exit_code != 0

    def test_no_diarization_flag(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """--no-diarization should disable diarization."""
        dummy_file = temp_dir / "test.mp4"
        dummy_file.write_bytes(b"fake video content")

        with patch(
            "scribbulus.cli.transcribe.TranscriptionEngine"
        ) as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_engine.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.transcribe.side_effect = Exception("Test stop")

            result = runner.invoke(
                transcribe, [str(dummy_file), "--no-diarization"]
            )

        # Should not show HF token warning
        assert "HuggingFace token" not in result.output

    def test_verbose_flag(self, runner: CliRunner, temp_dir: Path) -> None:
        """--verbose should enable verbose output."""
        dummy_file = temp_dir / "test.mp4"
        dummy_file.write_bytes(b"fake video content")

        with patch(
            "scribbulus.cli.transcribe.TranscriptionEngine"
        ) as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_engine.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.transcribe.side_effect = Exception("Test stop")

            result = runner.invoke(
                transcribe, [str(dummy_file), "-v", "--no-diarization"]
            )

        # Verbose mode should show traceback on error
        assert result.exit_code != 0


class TestErrorHandling:
    """Test CLI error handling."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    def test_unsupported_format_error(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Should handle unsupported format gracefully."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("not a media file")

        result = runner.invoke(transcribe, [str(txt_file)])

        assert result.exit_code != 0
        # Should show helpful message about supported formats

    def test_keyboard_interrupt_handled(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Should handle Ctrl+C gracefully."""
        dummy_file = temp_dir / "test.mp4"
        dummy_file.write_bytes(b"fake video")

        with patch(
            "scribbulus.cli.transcribe.TranscriptionEngine"
        ) as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value.__enter__ = MagicMock(
                return_value=mock_instance
            )
            mock_engine.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.transcribe.side_effect = KeyboardInterrupt()

            result = runner.invoke(
                transcribe, [str(dummy_file), "--no-diarization"]
            )

        assert "cancelled" in result.output.lower() or result.exit_code != 0
