"""Create responses using Copilot Responses API."""

import httpx
import json
import logging
from typing import List, Optional, Dict, Any, Union, AsyncIterator, Literal
from pydantic import BaseModel, Field

from ...lib.api_config import copilot_headers, copilot_base_url
from ...lib.state import state
from ...lib.error import HTTPError

logger = logging.getLogger(__name__)


# Type definitions
class ResponseInputText(BaseModel):
    """Text content in input."""
    type: Literal["input_text", "output_text"]
    text: str


class ResponseInputImage(BaseModel):
    """Image content in input."""
    type: Literal["input_image"]
    image_url: Optional[str] = None
    file_id: Optional[str] = None
    detail: Literal["low", "high", "auto"] = "auto"


ResponseInputContent = Union[ResponseInputText, ResponseInputImage, Dict[str, Any]]


class ResponseInputMessage(BaseModel):
    """Message in input array."""
    type: Literal["message"] = "message"
    role: Literal["user", "assistant", "system", "developer"]
    content: Optional[Union[str, List[ResponseInputContent]]] = None
    status: Optional[str] = None


class ResponseFunctionToolCallItem(BaseModel):
    """Function call in input."""
    type: Literal["function_call"]
    call_id: str
    name: str
    arguments: str
    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None


class ResponseFunctionCallOutputItem(BaseModel):
    """Function call output in input."""
    type: Literal["function_call_output"]
    call_id: str
    output: Union[str, List[ResponseInputContent]]
    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None


class ResponseInputReasoning(BaseModel):
    """Reasoning block in input."""
    id: Optional[str] = None
    type: Literal["reasoning"]
    summary: List[Dict[str, str]]
    encrypted_content: str


ResponseInputItem = Union[
    ResponseInputMessage,
    ResponseFunctionToolCallItem,
    ResponseFunctionCallOutputItem,
    ResponseInputReasoning,
    Dict[str, Any]
]


class FunctionTool(BaseModel):
    """Function tool definition."""
    name: str
    parameters: Optional[Dict[str, Any]] = None
    strict: Optional[bool] = None
    type: Literal["function"] = "function"
    description: Optional[str] = None


class ToolChoiceFunction(BaseModel):
    """Tool choice with specific function."""
    name: str
    type: Literal["function"] = "function"


ToolChoiceOptions = Literal["none", "auto", "required"]
ToolChoice = Union[ToolChoiceOptions, ToolChoiceFunction]


class Reasoning(BaseModel):
    """Reasoning configuration."""
    effort: Optional[Literal["minimal", "low", "medium", "high"]] = None
    summary: Optional[Literal["auto", "concise", "detailed"]] = None


ResponseIncludable = Literal[
    "file_search_call.results",
    "message.input_image.image_url",
    "computer_call_output.output.image_url",
    "reasoning.encrypted_content",
    "code_interpreter_call.outputs"
]


class ResponsesPayload(BaseModel):
    """Responses API request payload."""
    model: str
    instructions: Optional[str] = None
    input: Optional[Union[str, List[ResponseInputItem]]] = None
    tools: Optional[List[FunctionTool]] = None
    tool_choice: Optional[ToolChoice] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_output_tokens: Optional[int] = None
    metadata: Optional[Dict[str, str]] = None
    stream: Optional[bool] = None
    safety_identifier: Optional[str] = None
    prompt_cache_key: Optional[str] = None
    parallel_tool_calls: Optional[bool] = None
    store: Optional[bool] = None
    reasoning: Optional[Reasoning] = None
    include: Optional[List[ResponseIncludable]] = None
    previous_response_id: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


# Response types
class ResponseOutputText(BaseModel):
    """Text output content."""
    type: Literal["output_text"]
    text: str
    annotations: List[Any] = Field(default_factory=list)


class ResponseOutputRefusal(BaseModel):
    """Refusal output content."""
    type: Literal["refusal"]
    refusal: str


ResponseOutputContentBlock = Union[ResponseOutputText, ResponseOutputRefusal, Dict[str, Any]]


class ResponseOutputMessage(BaseModel):
    """Message output item."""
    id: str
    type: Literal["message"]
    role: Literal["assistant"]
    status: Literal["completed", "in_progress", "incomplete"]
    content: Optional[List[ResponseOutputContentBlock]] = None


class ResponseReasoningBlock(BaseModel):
    """Reasoning summary block."""
    type: str
    text: Optional[str] = None


class ResponseOutputReasoning(BaseModel):
    """Reasoning output item."""
    id: str
    type: Literal["reasoning"]
    summary: Optional[List[ResponseReasoningBlock]] = None
    encrypted_content: Optional[str] = None
    status: Optional[Literal["completed", "in_progress", "incomplete"]] = None


class ResponseOutputFunctionCall(BaseModel):
    """Function call output item."""
    id: Optional[str] = None
    type: Literal["function_call"]
    call_id: str
    name: str
    arguments: str
    status: Optional[Literal["in_progress", "completed", "incomplete"]] = None


ResponseOutputItem = Union[
    ResponseOutputMessage,
    ResponseOutputReasoning,
    ResponseOutputFunctionCall,
    Dict[str, Any]
]


class IncompleteDetails(BaseModel):
    """Details about incomplete response."""
    reason: Optional[Literal["max_output_tokens", "content_filter"]] = None


class ResponseError(BaseModel):
    """Error in response."""
    message: str


class ResponseUsage(BaseModel):
    """Token usage information."""
    input_tokens: int
    output_tokens: Optional[int] = None
    total_tokens: int
    input_tokens_details: Optional[Dict[str, int]] = None
    output_tokens_details: Optional[Dict[str, int]] = None


class ResponsesResult(BaseModel):
    """Responses API result."""
    id: str
    object: Literal["response"]
    created_at: int
    model: str
    output: List[ResponseOutputItem]
    output_text: str
    status: str
    usage: Optional[ResponseUsage] = None
    error: Optional[ResponseError] = None
    incomplete_details: Optional[IncompleteDetails] = None
    instructions: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    parallel_tool_calls: bool
    temperature: Optional[float] = None
    tool_choice: Optional[Any] = None
    tools: List[FunctionTool]
    top_p: Optional[float] = None
    
    class Config:
        extra = "allow"


# Stream event types
class ResponseStreamEvent(BaseModel):
    """Base stream event."""
    type: str
    sequence_number: int
    
    class Config:
        extra = "allow"


class ResponsesRequestOptions(BaseModel):
    """Options for responses request."""
    vision: bool
    initiator: Literal["agent", "user"]


async def create_responses(
    payload: ResponsesPayload,
    options: ResponsesRequestOptions
) -> Union[ResponsesResult, AsyncIterator[Dict[str, Any]]]:
    """Create responses using Copilot Responses API."""
    if not state.copilot_token:
        raise ValueError("Copilot token not found")
    
    # Build headers
    headers = {
        **copilot_headers(state, options.vision),
        "X-Initiator": options.initiator,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{copilot_base_url(state)}/responses",
            headers=headers,
            json=payload.dict(exclude_none=True),
            timeout=60.0,
        )
        
        if not response.is_success:
            logger.error(f"Failed to create responses: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise HTTPError("Failed to create responses", response)
        
        if payload.stream:
            return _stream_response(response)
        else:
            return ResponsesResult(**response.json())


async def _stream_response(response: httpx.Response) -> AsyncIterator[Dict[str, Any]]:
    """Process streaming response."""
    async for line in response.aiter_lines():
        if not line:
            continue
            
        # Handle SSE format
        if line.startswith("event: "):
            event_type = line[7:]
            continue
        elif line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON: {data}")
                continue


def get_responses_request_options(payload: ResponsesPayload) -> ResponsesRequestOptions:
    """Determine request options from payload."""
    vision = has_vision_input(payload)
    initiator = "agent" if has_agent_initiator(payload) else "user"
    
    return ResponsesRequestOptions(vision=vision, initiator=initiator)


def has_agent_initiator(payload: ResponsesPayload) -> bool:
    """Check if payload has agent initiator."""
    items = get_payload_items(payload)
    
    for item in items:
        if isinstance(item, dict):
            role = item.get("role")
            if not role:
                return True
            if isinstance(role, str) and role.lower() == "assistant":
                return True
        elif hasattr(item, "role"):
            if not item.role:
                return True
            if item.role.lower() == "assistant":
                return True
    
    return False


def has_vision_input(payload: ResponsesPayload) -> bool:
    """Check if payload contains vision input."""
    items = get_payload_items(payload)
    return any(contains_vision_content(item) for item in items)


def get_payload_items(payload: ResponsesPayload) -> List[Any]:
    """Extract items from payload input."""
    if not payload.input:
        return []
    
    if isinstance(payload.input, list):
        return payload.input
    
    return []


def contains_vision_content(value: Any) -> bool:
    """Check if value contains vision content."""
    if not value:
        return False
    
    if isinstance(value, list):
        return any(contains_vision_content(entry) for entry in value)
    
    if not isinstance(value, dict) and not hasattr(value, "__dict__"):
        return False
    
    # Convert to dict if it's an object
    if hasattr(value, "__dict__"):
        record = value.__dict__
    else:
        record = value
    
    # Check type field
    value_type = record.get("type", "")
    if isinstance(value_type, str) and value_type.lower() == "input_image":
        return True
    
    # Check content field
    content = record.get("content")
    if isinstance(content, list):
        return any(contains_vision_content(entry) for entry in content)
    
    return False
