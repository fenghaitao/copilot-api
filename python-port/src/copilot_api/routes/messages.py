"""Anthropic-compatible messages endpoint."""

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
from ..services.copilot.create_chat_completions import create_chat_completions, ChatCompletionsPayload, Message

logger = logging.getLogger(__name__)
router = APIRouter()


class AnthropicMessage(BaseModel):
    """Anthropic message format."""
    role: str
    content: Union[str, List[Dict[str, Any]]]


class AnthropicRequest(BaseModel):
    """Anthropic messages request format."""
    model: str
    max_tokens: int
    messages: List[AnthropicMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    system: Optional[str] = None


def convert_anthropic_to_openai(anthropic_request: AnthropicRequest) -> ChatCompletionsPayload:
    """Convert Anthropic request format to OpenAI format."""
    messages = []
    
    # Add system message if present
    if anthropic_request.system:
        messages.append(Message(role="system", content=anthropic_request.system))
    
    # Convert messages
    for msg in anthropic_request.messages:
        # Map Anthropic roles to OpenAI roles
        role = msg.role
        if role == "human":
            role = "user"
        elif role == "assistant":
            role = "assistant"
        
        messages.append(Message(role=role, content=msg.content))
    
    return ChatCompletionsPayload(
        model=anthropic_request.model,
        messages=messages,
        max_tokens=anthropic_request.max_tokens,
        temperature=anthropic_request.temperature,
        top_p=anthropic_request.top_p,
        stop=anthropic_request.stop_sequences,
        stream=anthropic_request.stream,
    )


def convert_openai_to_anthropic(openai_response: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAI response format to Anthropic format."""
    if "choices" in openai_response:
        # Non-streaming response
        choice = openai_response["choices"][0]
        message = choice["message"]
        
        return {
            "id": openai_response.get("id"),
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": message.get("content", "")}],
            "model": openai_response.get("model"),
            "stop_reason": "end_turn" if choice.get("finish_reason") == "stop" else "max_tokens",
            "stop_sequence": None,
            "usage": {
                "input_tokens": openai_response.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": openai_response.get("usage", {}).get("completion_tokens", 0),
            }
        }
    else:
        # Streaming chunk
        return openai_response


@router.post("/")
async def handle_messages(request: AnthropicRequest):
    """Handle Anthropic-style messages requests."""
    await check_rate_limit(state)
    
    logger.debug(f"Anthropic request: {request}")
    
    if state.manual_approve:
        await await_approval()
    
    # Convert to OpenAI format
    openai_payload = convert_anthropic_to_openai(request)
    
    logger.info(f"Current token count: {get_token_count([msg.dict() for msg in openai_payload.messages])}")
    
    response = await create_chat_completions(openai_payload)
    
    # Check if response is streaming or non-streaming
    if hasattr(response, "__aiter__"):
        # Streaming response
        logger.debug("Streaming Anthropic response")
        
        async def generate():
            async for chunk in response:
                anthropic_chunk = convert_openai_to_anthropic(chunk)
                yield f"data: {json.dumps(anthropic_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(), 
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        # Non-streaming response
        anthropic_response = convert_openai_to_anthropic(response)
        logger.debug(f"Non-streaming Anthropic response: {anthropic_response}")
        return anthropic_response