"""Create embeddings using Copilot API."""

import httpx
from typing import List, Union, Dict, Any
from pydantic import BaseModel

from ...lib.api_config import copilot_headers, copilot_base_url
from ...lib.state import state
from ...lib.error import HTTPError


class EmbeddingRequest(BaseModel):
    """Embedding request payload."""
    input: Union[str, List[str]]
    model: str


class Embedding(BaseModel):
    """Single embedding data."""
    object: str
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    """Embedding response."""
    object: str
    data: List[Embedding]
    model: str
    usage: Dict[str, int]


async def create_embeddings(payload: EmbeddingRequest) -> Dict[str, Any]:
    """Create embeddings using Copilot API."""
    if not state.copilot_token:
        raise ValueError("Copilot token not found")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{copilot_base_url(state)}/embeddings",
            headers=copilot_headers(state),
            json=payload.dict(),
        )
        
        if not response.is_success:
            raise HTTPError("Failed to create embeddings", response)
        
        return response.json()