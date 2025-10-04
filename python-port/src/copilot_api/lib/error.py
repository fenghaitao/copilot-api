"""Custom error classes."""

import httpx


class HTTPError(Exception):
    """HTTP error with response context."""
    
    def __init__(self, message: str, response: httpx.Response):
        self.message = message
        self.response = response
        super().__init__(f"{message}: {response.status_code} {response.reason_phrase}")
    
    async def get_response_json(self):
        """Get JSON response body."""
        try:
            return response.json()
        except Exception:
            return {"error": "Unable to parse response JSON"}


class CopilotAPIError(Exception):
    """Base exception for Copilot API errors."""
    pass


class AuthenticationError(CopilotAPIError):
    """Authentication related errors."""
    pass


class RateLimitError(CopilotAPIError):
    """Rate limiting errors."""
    pass