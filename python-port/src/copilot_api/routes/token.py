"""Token endpoint."""

from fastapi import APIRouter
from ..lib.state import state

router = APIRouter()


@router.get("/")
async def get_token_info():
    """Get token information."""
    return {"has_github_token": bool(state.github_token), "has_copilot_token": bool(state.copilot_token)}