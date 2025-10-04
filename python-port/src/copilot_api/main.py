#!/usr/bin/env python3
"""Main CLI entry point for Copilot API."""

import click
from rich.console import Console

from .commands.auth import auth_command
from .commands.start import start_command
from .commands.check_usage import check_usage_command
from .commands.debug import debug_command

console = Console()


@click.group()
@click.version_option()
def cli():
    """A wrapper around GitHub Copilot API to make it OpenAI compatible, making it usable for other tools."""
    pass


cli.add_command(auth_command, name="auth")
cli.add_command(start_command, name="start")
cli.add_command(check_usage_command, name="check-usage")
cli.add_command(debug_command, name="debug")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()