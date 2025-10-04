"""Rate limiting functionality."""

import asyncio
import time
from typing import TYPE_CHECKING

from .error import RateLimitError

if TYPE_CHECKING:
    from .state import State


async def check_rate_limit(state: "State") -> None:
    """Check and enforce rate limiting."""
    if state.rate_limit_seconds is None:
        return
    
    current_time = time.time()
    
    if state.last_request_timestamp is not None:
        time_since_last = current_time - state.last_request_timestamp
        
        if time_since_last < state.rate_limit_seconds:
            wait_time = state.rate_limit_seconds - time_since_last
            
            if state.rate_limit_wait:
                await asyncio.sleep(wait_time)
            else:
                raise RateLimitError(f"Rate limit exceeded. Wait {wait_time:.1f} seconds.")
    
    state.last_request_timestamp = current_time