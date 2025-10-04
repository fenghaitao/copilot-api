"""Manual approval functionality."""

import asyncio
from rich.console import Console
from rich.prompt import Confirm

console = Console()


async def await_approval() -> None:
    """Wait for manual approval of request."""
    def get_approval():
        return Confirm.ask("🤔 Approve this request?", default=True)
    
    # Run the blocking prompt in a thread pool
    loop = asyncio.get_event_loop()
    approved = await loop.run_in_executor(None, get_approval)
    
    if not approved:
        console.print("❌ Request denied by user", style="red")
        raise Exception("Request denied by user")