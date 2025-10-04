"""GitHub Copilot usage statistics retrieval."""

import httpx
from typing import Dict, Any

from ...lib.api_config import GITHUB_API_BASE_URL, github_headers
from ...lib.state import state
from ...lib.error import HTTPError


async def get_copilot_usage() -> Dict[str, Any]:
    """Get Copilot usage statistics from GitHub."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE_URL}/copilot_internal/user",
            headers=github_headers(state),
        )
        
        if not response.is_success:
            raise HTTPError("Failed to get Copilot usage", response)
        
        return response.json()