"""Main CLI entry point for scribbulus."""

import click

from scribbulus.cli.transcribe import transcribe


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(package_name="scribbulus")
def cli(ctx: click.Context) -> None:
    """
    Scribbulus - Production-grade media transcription with speaker diarization.

    Use 'scribbulus COMMAND --help' for command-specific help.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(transcribe)


if __name__ == "__main__":
    cli()
