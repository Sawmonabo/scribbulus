"""Main CLI entry point for scribbulus."""

import click

from scribbulus.cli.transcribe import transcribe
from scribbulus.transcription.audio_backend import configure_audio_backend


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(package_name="scribbulus")
def cli(ctx: click.Context) -> None:
    """
    Scribbulus - Production-grade media transcription with speaker diarization.

    Use 'scribbulus COMMAND --help' for command-specific help.
    """
    # Configure audio backend at app entry, before any subcommand runs
    configure_audio_backend()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(transcribe)


if __name__ == "__main__":
    cli()
