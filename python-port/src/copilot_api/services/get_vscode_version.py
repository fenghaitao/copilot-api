"""Get VS Code version from GitHub releases."""

import httpx
from typing import Dict, Any


async def get_vscode_version() -> str:
    """Get latest VS Code version from GitHub API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/repos/microsoft/vscode/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            if response.is_success:
                data = response.json()
                # Remove 'v' prefix if present
                version = data["tag_name"].lstrip("v")
                return version
            else:
                # Fallback version
                return "1.85.0"
    except Exception:
        # Fallback version
        return "1.85.0"