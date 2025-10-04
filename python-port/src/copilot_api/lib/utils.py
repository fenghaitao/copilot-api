"""Utility functions."""

import aiofiles
from rich.console import Console

from .paths import PATHS
from .state import state
from ..services.copilot.get_models import get_models
from ..services.get_vscode_version import get_vscode_version

console = Console()


async def cache_models():
    """Cache available models."""
    try:
        state.models = await get_models()
        console.print("✅ Models cached successfully", style="green")
    except Exception as error:
        console.print(f"⚠️  Failed to cache models: {error}", style="yellow")


async def cache_vscode_version():
    """Cache VS Code version."""
    try:
        # Try to read from cache first
        try:
            async with aiofiles.open(PATHS.vscode_version_path, "r") as f:
                state.vscode_version = (await f.read()).strip()
        except FileNotFoundError:
            # Fetch new version
            state.vscode_version = await get_vscode_version()
            # Cache it
            async with aiofiles.open(PATHS.vscode_version_path, "w") as f:
                await f.write(state.vscode_version)
        
        console.print(f"✅ VS Code version: {state.vscode_version}", style="green")
    except Exception as error:
        console.print(f"⚠️  Failed to get VS Code version, using default: {error}", style="yellow")
        state.vscode_version = "1.85.0"