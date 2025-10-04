"""Chat completions endpoint."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import json
import logging

from ..lib.state import state
from ..lib.rate_limit import check_rate_limit
from ..lib.approval import await_approval
from ..lib.tokenizer import get_token_count
from ..services.copilot.create_chat_completions import create_chat_completions, ChatCompletionsPayload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/")
async def handle_completion(payload: ChatCompletionsPayload):
    """Handle chat completion requests."""
    await check_rate_limit(state)
    
    logger.debug(f"Request payload: {str(payload)[-400:]}")
    logger.info(f"Current token count: {get_token_count(payload.messages)}")
    
    if state.manual_approve:
        await await_approval()
    
    # Set default max_tokens if not provided
    if payload.max_tokens is None and state.models:
        selected_model = next(
            (model for model in state.models["data"] if model["id"] == payload.model),
            None
        )
        if selected_model:
            payload.max_tokens = selected_model["capabilities"]["limits"]["max_output_tokens"]
            logger.debug(f"Set max_tokens to: {payload.max_tokens}")
    
    response = await create_chat_completions(payload)
    
    # Check if response is streaming or non-streaming
    if hasattr(response, "__aiter__"):
        # Streaming response
        logger.debug("Streaming response")
        
        async def generate():
            async for chunk in response:
                logger.debug(f"Streaming chunk: {chunk}")
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(), 
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        # Non-streaming response
        logger.debug(f"Non-streaming response: {response}")
        return response