"""Auth command implementation."""

import asyncio
import click
from rich.console import Console

from ..lib.paths import ensure_paths, PATHS
from ..lib.state import state
from ..lib.token import setup_github_token

console = Console()


async def run_auth(verbose: bool, show_token: bool):
    """Run GitHub authentication flow."""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("🔍 Verbose logging enabled", style="yellow")
    
    state.show_token = show_token
    
    await ensure_paths()
    await setup_github_token(force=True)
    console.print(f"✅ GitHub token written to {PATHS.github_token_path}", style="green")


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--show-token", is_flag=True, help="Show GitHub token on auth")
def auth_command(verbose, show_token):
    """Run GitHub auth flow without running the server."""
    asyncio.run(run_auth(verbose, show_token))