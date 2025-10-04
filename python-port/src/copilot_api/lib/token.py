"""Token management for GitHub and Copilot authentication."""

import asyncio
from typing import Optional
from pathlib import Path

import aiofiles
from rich.console import Console

from .paths import PATHS
from .state import state
from .error import HTTPError, AuthenticationError
from ..services.github.get_copilot_token import get_copilot_token
from ..services.github.get_device_code import get_device_code
from ..services.github.get_user import get_github_user
from ..services.github.poll_access_token import poll_access_token

console = Console()


async def read_github_token() -> Optional[str]:
    """Read GitHub token from file."""
    try:
        async with aiofiles.open(PATHS.github_token_path, "r") as f:
            return (await f.read()).strip()
    except FileNotFoundError:
        return None


async def write_github_token(token: str) -> None:
    """Write GitHub token to file."""
    async with aiofiles.open(PATHS.github_token_path, "w") as f:
        await f.write(token)


async def setup_copilot_token() -> None:
    """Setup and manage Copilot token with auto-refresh."""
    token_data = await get_copilot_token()
    state.copilot_token = token_data["token"]
    
    console.print("✓ GitHub Copilot Token fetched successfully!", style="green")
    if state.show_token:
        console.print(f"Copilot token: {token_data['token']}")
    
    # Setup refresh interval (refresh 60 seconds before expiry)
    refresh_interval = (token_data["refresh_in"] - 60)
    
    async def refresh_token():
        """Background task to refresh Copilot token."""
        await asyncio.sleep(refresh_interval)
        while True:
            try:
                console.print("🔄 Refreshing Copilot token...", style="yellow")
                new_token_data = await get_copilot_token()
                state.copilot_token = new_token_data["token"]
                console.print("✓ Copilot token refreshed", style="green")
                if state.show_token:
                    console.print(f"Refreshed Copilot token: {new_token_data['token']}")
                await asyncio.sleep(refresh_interval)
            except Exception as error:
                console.print(f"❌ Failed to refresh Copilot token: {error}", style="red")
                raise error
    
    # Start refresh task in background
    asyncio.create_task(refresh_token())


async def setup_github_token(force: bool = False) -> None:
    """Setup GitHub token with device flow authentication."""
    try:
        if not force:
            existing_token = await read_github_token()
            if existing_token:
                state.github_token = existing_token
                if state.show_token:
                    console.print(f"GitHub token: {existing_token}")
                await log_user()
                return
        
        console.print("🔐 Not logged in, getting new access token...", style="yellow")
        device_response = await get_device_code()
        
        console.print(
            f"📱 Please enter the code \"{device_response['user_code']}\" "
            f"at {device_response['verification_uri']}", 
            style="bold blue"
        )
        
        token = await poll_access_token(device_response)
        await write_github_token(token)
        state.github_token = token
        
        if state.show_token:
            console.print(f"GitHub token: {token}")
        
        await log_user()
        
    except HTTPError as error:
        console.print(f"❌ Failed to get GitHub token: {error}", style="red")
        raise error
    except Exception as error:
        console.print(f"❌ Failed to get GitHub token: {error}", style="red")
        raise error


async def log_user() -> None:
    """Log the current authenticated user."""
    try:
        user = await get_github_user()
        console.print(f"👤 Logged in as {user['login']}", style="green")
    except Exception as error:
        console.print(f"⚠️  Could not fetch user info: {error}", style="yellow")