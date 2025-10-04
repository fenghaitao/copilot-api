"""Embeddings endpoint."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
import json

from ..lib.state import state
from ..lib.rate_limit import check_rate_limit
from ..lib.approval import await_approval
from ..services.copilot.create_embeddings import create_embeddings, EmbeddingRequest
from ..lib.error import HTTPError

logger = logging.getLogger(__name__)
router = APIRouter()


async def forward_error(error: Exception) -> JSONResponse:
    """Forward error response similar to TypeScript forwardError function."""
    logger.error(f"Error occurred: {error}")
    
    if isinstance(error, HTTPError):
        try:
            error_text = await error.response.aread()
            error_text = error_text.decode('utf-8')
            try:
                error_json = json.loads(error_text)
            except json.JSONDecodeError:
                error_json = error_text
            
            logger.error(f"HTTP error: {error_json}")
            
            return JSONResponse(
                content={
                    "error": {
                        "message": error_text,
                        "type": "error",
                    },
                },
                status_code=error.response.status_code,
            )
        except Exception:
            # Fallback if we can't read the response
            return JSONResponse(
                content={
                    "error": {
                        "message": str(error),
                        "type": "error",
                    },
                },
                status_code=500,
            )
    
    return JSONResponse(
        content={
            "error": {
                "message": str(error),
                "type": "error",
            },
        },
        status_code=500,
    )


@router.post("/")
async def handle_embeddings(payload: EmbeddingRequest):
    """Handle embeddings requests - ports from TypeScript embeddingRoutes.post("/")."""
    try:
        await check_rate_limit(state)
        
        if state.manual_approve:
            await await_approval()
        
        response = await create_embeddings(payload)
        return response
        
    except Exception as error:
        return await forward_error(error)