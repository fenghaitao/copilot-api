"""Get available Copilot models."""

import httpx
from typing import Dict, Any

from ...lib.api_config import copilot_base_url, copilot_headers
from ...lib.state import state
from ...lib.error import HTTPError


async def get_models() -> Dict[str, Any]:
    """Get available Copilot models."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{copilot_base_url(state)}/models",
            headers=copilot_headers(state),
        )
        
        if not response.is_success:
            raise HTTPError("Failed to get models", response)
        
        return response.json()