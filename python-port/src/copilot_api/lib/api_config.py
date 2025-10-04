"""API configuration and headers."""

import uuid
from typing import Dict, Any

from .state import State

# Constants
COPILOT_VERSION = "0.26.7"
EDITOR_PLUGIN_VERSION = f"copilot-chat/{COPILOT_VERSION}"
USER_AGENT = f"GitHubCopilotChat/{COPILOT_VERSION}"
API_VERSION = "2025-04-01"

GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_BASE_URL = "https://github.com"
GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"
GITHUB_APP_SCOPES = "read:user"


def standard_headers() -> Dict[str, str]:
    """Standard HTTP headers."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
    }


def copilot_base_url(state: State) -> str:
    """Get Copilot API base URL based on account type."""
    if state.account_type == "individual":
        return "https://api.githubcopilot.com"
    return f"https://api.{state.account_type}.githubcopilot.com"


def copilot_headers(state: State, vision: bool = False) -> Dict[str, str]:
    """Generate headers for Copilot API requests."""
    headers = {
        "Authorization": f"Bearer {state.copilot_token}",
        "content-type": "application/json",
        "copilot-integration-id": "vscode-chat",
        "editor-version": f"vscode/{state.vscode_version}",
        "editor-plugin-version": EDITOR_PLUGIN_VERSION,
        "user-agent": USER_AGENT,
        "openai-intent": "conversation-panel",
        "x-github-api-version": API_VERSION,
        "x-request-id": str(uuid.uuid4()),
        "x-vscode-user-agent-library-version": "electron-fetch",
    }
    
    if vision:
        headers["copilot-vision-request"] = "true"
    
    return headers


def github_headers(state: State) -> Dict[str, str]:
    """Generate headers for GitHub API requests."""
    return {
        **standard_headers(),
        "authorization": f"token {state.github_token}",
        "editor-version": f"vscode/{state.vscode_version}",
        "editor-plugin-version": EDITOR_PLUGIN_VERSION,
        "user-agent": USER_AGENT,
        "x-github-api-version": API_VERSION,
        "x-vscode-user-agent-library-version": "electron-fetch",
    }