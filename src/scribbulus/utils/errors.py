"""Custom exceptions for scribbulus."""

from __future__ import annotations


class ScribbulusError(Exception):
    """Base exception for all scribbulus errors."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        """
        :param message: Error message.
        :param exit_code: Exit code for the error.
        """
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class FFmpegNotFoundError(ScribbulusError):
    """Raised when ffmpeg is not found on the system."""

    def __init__(self, message: str | None = None) -> None:
        """
        :param message: Custom error message. If None, uses default message.
        """
        default_message = (
            "FFmpeg not found. Please install ffmpeg:\n"
            "  macOS:        brew install ffmpeg\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  Fedora:       sudo dnf install ffmpeg\n"
            "  Or run:       make install-ffmpeg"
        )
        super().__init__(message or default_message, exit_code=5)


class FFprobeError(ScribbulusError):
    """Raised when ffprobe fails to analyze a file."""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        """
        :param message: Error message.
        :param file_path: Path to the file that failed analysis.
        """
        if file_path:
            message = f"Failed to analyze '{file_path}': {message}"
        super().__init__(message, exit_code=1)


class UnsupportedFormatError(ScribbulusError):
    """Raised when the input file format is not supported."""

    def __init__(
        self, file_path: str, detected_format: str | None = None
    ) -> None:
        """
        :param file_path: Path to the unsupported file.
        :param detected_format: The detected file format.
        """
        if detected_format:
            message = (
                f"Unsupported format '{detected_format}' for file: {file_path}"
            )
        else:
            message = f"Unsupported file format: {file_path}"
        super().__init__(message, exit_code=3)


class NoAudioStreamError(ScribbulusError):
    """Raised when a media file contains no audio stream."""

    def __init__(self, file_path: str) -> None:
        """
        :param file_path: Path to the file with no audio stream.
        """
        message = f"No audio stream found in file: {file_path}"
        super().__init__(message, exit_code=4)


class FileNotFoundError(ScribbulusError):
    """Raised when the input file is not found."""

    def __init__(self, file_path: str) -> None:
        """
        :param file_path: Path to the file that was not found.
        """
        message = f"File not found: {file_path}"
        super().__init__(message, exit_code=2)


class AudioExtractionError(ScribbulusError):
    """Raised when audio extraction fails."""

    def __init__(self, message: str, file_path: str | None = None) -> None:
        """
        :param message: Error message.
        :param file_path: Path to the file from which audio extraction failed.
        """
        if file_path:
            message = f"Failed to extract audio from '{file_path}': {message}"
        super().__init__(message, exit_code=1)


class TranscriptionError(ScribbulusError):
    """Raised when transcription fails."""

    def __init__(self, message: str) -> None:
        """
        :param message: Error message.
        """
        super().__init__(f"Transcription failed: {message}", exit_code=6)


class DiarizationError(ScribbulusError):
    """Raised when speaker diarization fails."""

    def __init__(self, message: str) -> None:
        """
        :param message: Error message.
        """
        super().__init__(f"Diarization failed: {message}", exit_code=7)


class ModelNotFoundError(ScribbulusError):
    """Raised when a Whisper model cannot be found or loaded."""

    def __init__(self, model_name: str, message: str | None = None) -> None:
        """
        :param model_name: Name of the model that failed to load.
        :param message: Additional error message.
        """
        default_message = f"Failed to load model '{model_name}'"
        if message:
            default_message = f"{default_message}: {message}"
        super().__init__(default_message, exit_code=1)


class HuggingFaceTokenError(ScribbulusError):
    """Raised when HuggingFace token is required but not provided."""

    def __init__(self) -> None:
        message = (
            "HuggingFace token required for speaker diarization.\n"
            "Set the HF_TOKEN environment variable or use --hf-token option.\n"
            "Get your token at: https://huggingface.co/settings/tokens"
        )
        super().__init__(message, exit_code=1)
