"""Token counting functionality."""

import tiktoken
from typing import List, Dict, Any, Union


def get_token_count(messages: List[Dict[str, Any]]) -> int:
    """Get token count for messages using tiktoken."""
    try:
        # Use GPT-4 tokenizer as a reasonable approximation
        encoding = tiktoken.get_encoding("cl100k_base")
        
        total_tokens = 0
        for message in messages:
            # Count tokens in role
            total_tokens += len(encoding.encode(message.get("role", "")))
            
            # Count tokens in content
            content = message.get("content", "")
            if isinstance(content, str):
                total_tokens += len(encoding.encode(content))
            elif isinstance(content, list):
                # Handle multimodal content
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text", "")
                        total_tokens += len(encoding.encode(text))
                    # Note: Image tokens are harder to estimate, skipping for now
        
        return total_tokens
    except Exception:
        # Fallback to rough estimation
        return sum(len(str(msg).split()) for msg in messages) * 2