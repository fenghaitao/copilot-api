"""Usage endpoint (placeholder)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_usage():
    """Get usage statistics (placeholder implementation)."""
    return {"usage": {"total_requests": 0, "total_tokens": 0}}