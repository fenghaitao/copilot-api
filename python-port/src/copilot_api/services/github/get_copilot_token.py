"""GitHub Copilot token retrieval."""

import httpx
from typing import Dict, Any

from ...lib.api_config import GITHUB_API_BASE_URL, github_headers
from ...lib.state import state
from ...lib.error import HTTPError


async def get_copilot_token() -> Dict[str, Any]:
    """Get Copilot API token from GitHub."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE_URL}/copilot_internal/v2/token",
            headers=github_headers(state),
        )
        
        if not response.is_success:
            raise HTTPError("Failed to get Copilot token", response)
        
        return response.json()