"""GitHub Copilot usage statistics retrieval."""

import httpx
from typing import Dict, Any, Optional

from ...lib.api_config import GITHUB_API_BASE_URL, github_headers
from ...lib.state import state
from ...lib.error import HTTPError


async def get_copilot_usage(since: Optional[str] = None, until: Optional[str] = None) -> Dict[str, Any]:
    """Get Copilot usage statistics from GitHub.
    
    Args:
        since: Show usage since this date (YYYY-MM-DD format)
        until: Show usage until this date (YYYY-MM-DD format)
    
    Returns:
        Usage data dict or list of daily metrics if date range specified
    """
    async with httpx.AsyncClient() as client:
        # If date range specified, use organization metrics API
        if since or until:
            # First, get user info to find their organization
            user_response = await client.get(
                f"{GITHUB_API_BASE_URL}/copilot_internal/user",
                headers=github_headers(state),
            )
            
            if not user_response.is_success:
                raise HTTPError("Failed to get user info", user_response)
            
            user_data = user_response.json()
            org_list = user_data.get("organization_login_list", [])
            
            if not org_list:
                raise ValueError("No organization found. Historical usage requires organization membership.")
            
            # Use the first organization
            org = org_list[0]
            
            # Build query parameters
            params = {}
            if since:
                params["since"] = f"{since}T00:00:00Z"
            if until:
                params["until"] = f"{until}T23:59:59Z"
            
            # Query organization usage metrics
            # Note: This requires organization owner or billing manager permissions
            # The correct endpoint is /orgs/{org}/copilot/metrics (not /usage)
            response = await client.get(
                f"{GITHUB_API_BASE_URL}/orgs/{org}/copilot/metrics",
                headers=github_headers(state),
                params=params,
            )
            
            if response.status_code == 403:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", "Permission denied")
                except:
                    error_msg = "Permission denied"
                
                # Provide helpful guidance
                raise ValueError(
                    f"{error_msg}.\n\n"
                    f"To view usage metrics for organization '{org}', you need:\n"
                    f"  1. Organization owner or billing manager role\n"
                    f"  2. A personal access token with 'copilot' or 'manage_billing:copilot' scope\n"
                    f"  3. The Copilot metrics API access policy enabled for your organization\n\n"
                    f"See: https://docs.github.com/en/rest/copilot/copilot-metrics"
                )
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", "Bad Request")
                    errors = error_data.get("errors", "")
                    if errors:
                        error_msg = f"{error_msg}: {errors}"
                except:
                    error_msg = "Bad Request"
                raise ValueError(f"Invalid request: {error_msg}")
            elif not response.is_success:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}"
                raise HTTPError(f"Failed to get organization usage metrics for '{org}': {error_msg}", response)
            
            return response.json()
        
        # Default: current quota
        response = await client.get(
            f"{GITHUB_API_BASE_URL}/copilot_internal/user",
            headers=github_headers(state),
        )
        
        if not response.is_success:
            raise HTTPError("Failed to get Copilot usage", response)
        
        return response.json()