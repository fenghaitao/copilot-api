"""Create chat completions using Copilot API."""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any, Union, AsyncIterator
from pydantic import BaseModel

from ...lib.api_config import copilot_headers, copilot_base_url
from ...lib.state import state
from ...lib.error import HTTPError

logger = logging.getLogger(__name__)


class ContentPart(BaseModel):
    """Content part for multimodal messages."""
    type: str
    text: Optional[str] = None
    image_url: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Chat message."""
    role: str
    content: Union[str, List[ContentPart], None]
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class Tool(BaseModel):
    """Function tool definition."""
    type: str
    function: Dict[str, Any]


class ChatCompletionsPayload(BaseModel):
    """Chat completions request payload."""
    messages: List[Message]
    model: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[bool] = None
    response_format: Optional[Dict[str, str]] = None
    seed: Optional[int] = None
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    user: Optional[str] = None


async def create_chat_completions(payload: ChatCompletionsPayload) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
    """Create chat completions using Copilot API."""
    if not state.copilot_token:
        raise ValueError("Copilot token not found")
    
    # Check for vision capability
    enable_vision = any(
        isinstance(msg.content, list) and 
        any(part.type == "image_url" for part in msg.content if hasattr(part, 'type'))
        for msg in payload.messages
        if isinstance(msg.content, list)
    )
    
    # Check if any message is from an agent (assistant or tool)
    is_agent_call = any(msg.role in ["assistant", "tool"] for msg in payload.messages)
    
    # Build headers
    headers = {
        **copilot_headers(state, enable_vision),
        "X-Initiator": "agent" if is_agent_call else "user",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{copilot_base_url(state)}/chat/completions",
            headers=headers,
            json=payload.dict(exclude_none=True),
        )
        
        if not response.is_success:
            logger.error(f"Failed to create chat completions: {response.status_code}")
            raise HTTPError("Failed to create chat completions", response)
        
        if payload.stream:
            return _stream_response(response)
        else:
            return response.json()


async def _stream_response(response: httpx.Response) -> AsyncIterator[Dict[str, Any]]:
    """Process streaming response."""
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            data = line[6:]  # Remove "data: " prefix
            if data == "[DONE]":
                break
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON: {data}")
                continue