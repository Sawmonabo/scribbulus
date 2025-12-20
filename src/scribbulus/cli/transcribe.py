"""CLI entrypoint for transcription."""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, cast

import click

from scribbulus.transcription.engine import (
    EngineConfig,
    TranscriptionEngine,
    TranscriptionOutput,
)
from scribbulus.utils.errors import (
    FFmpegNotFoundError,
    NoAudioStreamError,
    ScribbulusError,
    TranscriptionError,
    UnsupportedFormatError,
)
from scribbulus.utils.progress import create_stage_callback
from scribbulus.utils.types import ComputeType, DeviceType

if TYPE_CHECKING:
    pass


# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_FILE_NOT_FOUND = 2
EXIT_UNSUPPORTED_FORMAT = 3
EXIT_NO_AUDIO = 4
EXIT_FFMPEG_NOT_FOUND = 5
EXIT_TRANSCRIPTION_FAILED = 6
EXIT_DIARIZATION_FAILED = 7


# Available model sizes
MODEL_CHOICES = [
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v1",
    "large-v2",
    "large-v3",
    "large-v3-turbo",
    "turbo",
    "distil-large-v2",
    "distil-large-v3",
    "distil-medium.en",
    "distil-small.en",
]


def setup_logging(verbose: bool) -> None:
    """
    Configure logging based on verbosity.

    :param verbose: Enable debug-level logging if True, warning-level if False.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def write_output(
    output: TranscriptionOutput,
    output_path: Path | None,
    include_speakers: bool,
    include_timestamps: bool,
) -> None:
    """
    Write transcription output to file or stdout.

    :param output: The transcription output to write.
    :param output_path: Path to output file, or None to write to stdout.
    :param include_speakers: Include speaker labels in the output.
    :param include_timestamps: Include timestamps in the output.
    """
    # Format the transcript
    transcript = output.format_transcript(
        include_speakers=include_speakers,
        include_timestamps=include_timestamps,
    )

    if output_path:
        output_path.write_text(transcript, encoding="utf-8")
        click.echo(f"\nTranscript saved to: {output_path}", err=True)
    else:
        # Output to stdout
        click.echo(transcript)


@click.command("transcribe")
@click.argument(
    "input_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output .txt file path. If not specified, prints to stdout.",
)
@click.option(
    "-l",
    "--language",
    type=str,
    default=None,
    help="Language code (e.g., 'en', 'es'). Auto-detects if not specified.",
)
@click.option(
    "--model",
    "model_size",
    type=click.Choice(MODEL_CHOICES, case_sensitive=False),
    default="large-v3-turbo",
    help="Whisper model size. Larger models are more accurate but slower.",
)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "cpu"], case_sensitive=False),
    default="auto",
    help="Device for inference. 'auto' selects CUDA if available.",
)
@click.option(
    "--compute-type",
    type=click.Choice(
        ["float16", "float32", "int8_float16", "int8", "auto"],
        case_sensitive=False,
    ),
    default=None,
    help="Compute type for model. Default: float16 for GPU, int8 for CPU.",
)
@click.option(
    "--no-diarization",
    is_flag=True,
    default=False,
    help="Disable speaker diarization (faster processing).",
)
@click.option(
    "--num-speakers",
    type=int,
    default=None,
    help="Number of speakers (improves accuracy). Auto-detects if not set.",
)
@click.option(
    "--hf-token",
    type=str,
    envvar="HF_TOKEN",
    default=None,
    help="HuggingFace token for diarization. Also set via HF_TOKEN env var.",
)
@click.option(
    "--timestamps",
    is_flag=True,
    default=False,
    help="Include timestamps in output.",
)
@click.option(
    "--no-speakers",
    is_flag=True,
    default=False,
    help="Exclude speaker labels from output (even with diarization).",
)
@click.option(
    "--chunk-duration",
    type=float,
    default=30.0,
    help="Duration of audio chunks in seconds (for memory efficiency).",
)
@click.option(
    "--no-chunking",
    is_flag=True,
    default=False,
    help="Disable chunking (may use more memory for long files).",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output with progress details.",
)
@click.option(
    "--no-progress",
    "no_progress",
    is_flag=True,
    default=False,
    envvar="SCRIBBULUS_NO_PROGRESS",
    help="Disable progress bars (auto-disabled in CI/non-TTY).",
)
def transcribe(  # noqa: C901, PLR0912, PLR0913, PLR0915 - CLI entrypoint with Click options
    input_path: Path,
    output_path: Path | None,
    language: str | None,
    model_size: str,
    device: str,
    compute_type: str | None,
    no_diarization: bool,
    num_speakers: int | None,
    hf_token: str | None,
    timestamps: bool,
    no_speakers: bool,
    chunk_duration: float,
    no_chunking: bool,
    verbose: bool,
    no_progress: bool,
) -> None:
    """
    Transcribe audio/video files to text.

    INPUT_PATH is the path to the audio or video file to transcribe.

    Supported formats:
      Video: MP4, MOV, MKV, AVI, WebM
      Audio: WAV, MP3, M4A, FLAC, OGG, AAC

    Examples:
      scribbulus transcribe video.mp4
      scribbulus transcribe interview.mov -o transcript.txt
      scribbulus transcribe podcast.mp3 --no-diarization
      scribbulus transcribe meeting.mp4 -l en --num-speakers 3
    """
    setup_logging(verbose)

    # Validate diarization requirements
    enable_diarization = not no_diarization
    if enable_diarization and not hf_token:
        click.echo(
            "Warning: Speaker diarization requires a HuggingFace token.\n"
            "Set HF_TOKEN environment variable or use --hf-token option.\n"
            "Continuing without diarization...\n",
            err=True,
        )
        enable_diarization = False

    # Build configuration
    config = EngineConfig(
        model_size=model_size,  # type: ignore[arg-type]
        device=cast(DeviceType, device),
        compute_type=cast(ComputeType, compute_type) if compute_type else None,
        language=language,
        word_timestamps=True,
        enable_diarization=enable_diarization,
        hf_token=hf_token,
        num_speakers=num_speakers,
        chunk_duration_sec=chunk_duration,
        enable_chunking=not no_chunking,
    )

    # Create progress callback
    # disable=True forces off, disable=None auto-detects TTY
    progress_disabled = True if no_progress else None
    progress_callback = create_stage_callback(disable=progress_disabled)

    try:
        click.echo(f"Transcribing: {input_path.name}", err=True)
        click.echo(f"Model: {model_size}", err=True)

        if enable_diarization:
            click.echo("Speaker diarization: enabled", err=True)
        else:
            click.echo("Speaker diarization: disabled", err=True)

        click.echo("", err=True)

        # Run transcription
        with TranscriptionEngine(
            config=config,
            progress_callback=progress_callback,
        ) as engine:
            output = engine.transcribe(input_path)

        # Print summary
        click.echo("", err=True)
        click.echo("--- Summary ---", err=True)
        click.echo(f"Duration: {_format_duration(output.duration)}", err=True)
        click.echo(f"Language: {output.language}", err=True)

        if output.has_diarization and output.speakers:
            click.echo(f"Speakers: {len(output.speakers)} detected", err=True)

        # Write output
        write_output(
            output,
            output_path,
            include_speakers=not no_speakers and output.has_diarization,
            include_timestamps=timestamps,
        )

        sys.exit(EXIT_SUCCESS)

    except FileNotFoundError as e:
        click.echo(f"Error: File not found - {e}", err=True)
        sys.exit(EXIT_FILE_NOT_FOUND)

    except UnsupportedFormatError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "Supported: MP4, MOV, MKV, AVI, WebM, WAV, MP3, M4A, FLAC, OGG",
            err=True,
        )
        sys.exit(EXIT_UNSUPPORTED_FORMAT)

    except NoAudioStreamError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_NO_AUDIO)

    except FFmpegNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "\nInstall ffmpeg:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  Fedora: sudo dnf install ffmpeg",
            err=True,
        )
        sys.exit(EXIT_FFMPEG_NOT_FOUND)

    except TranscriptionError as e:
        click.echo(f"Error: Transcription failed - {e}", err=True)
        sys.exit(EXIT_TRANSCRIPTION_FAILED)

    except ScribbulusError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)

    except KeyboardInterrupt:
        click.echo("\nTranscription cancelled.", err=True)
        sys.exit(EXIT_ERROR)

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            click.echo(f"\nTraceback:\n{traceback.format_exc()}", err=True)
        sys.exit(EXIT_ERROR)


def _format_duration(seconds: float) -> str:
    """
    Format duration as HH:MM:SS or MM:SS.

    :param seconds: Duration in seconds.
    :returns: Formatted duration string.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    transcribe()
