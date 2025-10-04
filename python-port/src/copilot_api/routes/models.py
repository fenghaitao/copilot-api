"""Models endpoint."""

from fastapi import APIRouter
from ..lib.state import state

router = APIRouter()


@router.get("/")
async def get_models():
    """Get available models."""
    if state.models:
        return state.models
    return {"data": [], "object": "list"}