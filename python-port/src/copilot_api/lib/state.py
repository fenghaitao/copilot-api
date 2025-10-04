"""Application state management."""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import time


@dataclass
class State:
    """Global application state."""
    
    github_token: Optional[str] = None
    copilot_token: Optional[str] = None
    
    account_type: str = "individual"
    models: Optional[Dict[str, Any]] = None
    vscode_version: Optional[str] = None
    
    manual_approve: bool = False
    rate_limit_wait: bool = False
    show_token: bool = False
    
    # Rate limiting configuration
    rate_limit_seconds: Optional[int] = None
    last_request_timestamp: Optional[float] = None


# Global state instance
state = State()