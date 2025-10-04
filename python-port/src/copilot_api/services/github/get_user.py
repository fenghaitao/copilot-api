"""GitHub user information retrieval."""

import httpx
from typing import Dict, Any

from ...lib.api_config import GITHUB_API_BASE_URL, github_headers
from ...lib.state import state
from ...lib.error import HTTPError


async def get_github_user() -> Dict[str, Any]:
    """Get current GitHub user information."""
    async with httpx.AsyncClient() as client:
        # Use standard GitHub API headers without the newer API version
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "authorization": f"token {state.github_token}",
            "user-agent": "GitHubCopilotChat/0.26.7",
        }
        
        response = await client.get(
            f"{GITHUB_API_BASE_URL}/user",
            headers=headers,
        )
        
        if not response.is_success:
            raise HTTPError("Failed to get GitHub user", response)
        
        return response.json()