"""GitHub OAuth token polling."""

import asyncio
import httpx
from typing import Dict, Any

from ...lib.api_config import GITHUB_BASE_URL, GITHUB_CLIENT_ID
from ...lib.error import HTTPError


async def poll_access_token(device_response: Dict[str, Any]) -> str:
    """Poll for access token after user authorizes device."""
    device_code = device_response["device_code"]
    interval = device_response["interval"]
    expires_in = device_response["expires_in"]
    
    async with httpx.AsyncClient() as client:
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if we've exceeded the expiry time
            if asyncio.get_event_loop().time() - start_time > expires_in:
                raise HTTPError("Device code expired", httpx.Response(408))
            
            response = await client.post(
                f"{GITHUB_BASE_URL}/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
            
            if response.is_success:
                data = response.json()
                if "access_token" in data:
                    return data["access_token"]
                elif data.get("error") == "authorization_pending":
                    # User hasn't authorized yet, wait and try again
                    await asyncio.sleep(interval)
                    continue
                elif data.get("error") == "slow_down":
                    # We're polling too fast, increase interval
                    interval += 5
                    await asyncio.sleep(interval)
                    continue
                else:
                    # Some other error occurred
                    raise HTTPError(f"OAuth error: {data.get('error', 'unknown')}", response)
            else:
                raise HTTPError("Failed to poll access token", response)