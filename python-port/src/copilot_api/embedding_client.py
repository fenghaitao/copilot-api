"""
Standalone GitHub Copilot Embeddings Client

A simple, direct interface to GitHub Copilot's embedding API without requiring a server.
"""

import asyncio
import httpx
import os
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import aiofiles
from dataclasses import dataclass

from .lib.api_config import GITHUB_API_BASE_URL, GITHUB_BASE_URL, GITHUB_CLIENT_ID, GITHUB_APP_SCOPES
from .lib.paths import PATHS
from .lib.error import HTTPError


@dataclass
class EmbeddingResult:
    """Result from embedding operation."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]
    texts: List[str]
    
    def __len__(self) -> int:
        """Return number of embeddings."""
        return len(self.embeddings)
    
    def __getitem__(self, index: int) -> List[float]:
        """Get embedding by index."""
        return self.embeddings[index]


class CopilotEmbeddingClient:
    """Standalone GitHub Copilot Embeddings Client."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the embedding client.
        
        Args:
            github_token: GitHub token. If None, will try to load from config or prompt for auth.
        """
        self.github_token = github_token
        self.copilot_token: Optional[str] = None
        self.vscode_version = "1.85.0"
        
    async def _ensure_authenticated(self) -> None:
        """Ensure we have valid GitHub and Copilot tokens."""
        if not self.github_token:
            self.github_token = await self._get_github_token()
        
        if not self.copilot_token:
            self.copilot_token = await self._get_copilot_token()
    
    async def _get_github_token(self) -> str:
        """Get GitHub token from file or interactive auth."""
        # Try to read existing token
        try:
            async with aiofiles.open(PATHS.github_token_path, "r") as f:
                token = (await f.read()).strip()
                if token:
                    return token
        except FileNotFoundError:
            pass
        
        # Interactive authentication
        print("🔐 GitHub authentication required...")
        return await self._interactive_github_auth()
    
    async def _interactive_github_auth(self) -> str:
        """Interactive GitHub device flow authentication."""
        async with httpx.AsyncClient() as client:
            # Get device code
            response = await client.post(
                f"{GITHUB_BASE_URL}/login/device/code",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "scope": GITHUB_APP_SCOPES,
                },
                headers={"Accept": "application/json"},
            )
            
            if not response.is_success:
                raise HTTPError("Failed to get device code", response)
            
            device_data = response.json()
            
            print(f"📱 Please go to: {device_data['verification_uri']}")
            print(f"🔑 Enter code: {device_data['user_code']}")
            print("⏳ Waiting for authentication...")
            
            # Poll for token
            device_code = device_data["device_code"]
            interval = device_data["interval"]
            
            while True:
                await asyncio.sleep(interval)
                
                token_response = await client.post(
                    f"{GITHUB_BASE_URL}/login/oauth/access_token",
                    data={
                        "client_id": GITHUB_CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                )
                
                if token_response.is_success:
                    data = token_response.json()
                    if "access_token" in data:
                        token = data["access_token"]
                        
                        # Save token
                        PATHS.ensure_paths()
                        async with aiofiles.open(PATHS.github_token_path, "w") as f:
                            await f.write(token)
                        
                        print("✅ Authentication successful!")
                        return token
                    elif data.get("error") == "authorization_pending":
                        continue
                    elif data.get("error") == "slow_down":
                        interval += 5
                        continue
                    else:
                        raise Exception(f"Authentication error: {data.get('error')}")
    
    async def _get_copilot_token(self) -> str:
        """Get Copilot API token."""
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "authorization": f"token {self.github_token}",
            "editor-version": f"vscode/{self.vscode_version}",
            "editor-plugin-version": "copilot-chat/0.26.7",
            "user-agent": "GitHubCopilotChat/0.26.7",
            "x-github-api-version": "2025-04-01",
            "x-vscode-user-agent-library-version": "electron-fetch",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE_URL}/copilot_internal/v2/token",
                headers=headers,
            )
            
            if not response.is_success:
                raise HTTPError("Failed to get Copilot token", response)
            
            data = response.json()
            return data["token"]
    
    def _get_copilot_base_url(self, account_type: str = "individual") -> str:
        """Get Copilot API base URL."""
        if account_type == "individual":
            return "https://api.githubcopilot.com"
        return f"https://api.{account_type}.githubcopilot.com"
    
    def _get_copilot_headers(self) -> Dict[str, str]:
        """Get headers for Copilot API requests."""
        import uuid
        
        return {
            "Authorization": f"Bearer {self.copilot_token}",
            "content-type": "application/json",
            "copilot-integration-id": "vscode-chat",
            "editor-version": f"vscode/{self.vscode_version}",
            "editor-plugin-version": "copilot-chat/0.26.7",
            "user-agent": "GitHubCopilotChat/0.26.7",
            "openai-intent": "conversation-panel",
            "x-github-api-version": "2025-04-01",
            "x-request-id": str(uuid.uuid4()),
            "x-vscode-user-agent-library-version": "electron-fetch",
        }
    
    async def embed(
        self, 
        texts: Union[str, List[str]], 
        model: str = "text-embedding-3-small",
        account_type: str = "individual"
    ) -> EmbeddingResult:
        """
        Create embeddings for the given texts.
        
        Args:
            texts: Single text string or list of text strings to embed
            model: Embedding model to use (default: text-embedding-3-small)
            account_type: GitHub account type (individual, business, enterprise)
            
        Returns:
            EmbeddingResult with embeddings, model info, and usage data
        """
        await self._ensure_authenticated()
        
        # Ensure texts is a list
        if isinstance(texts, str):
            text_list = [texts]
        else:
            text_list = texts
        
        payload = {
            "input": text_list,
            "model": model
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._get_copilot_base_url(account_type)}/embeddings",
                headers=self._get_copilot_headers(),
                json=payload,
            )
            
            if not response.is_success:
                raise HTTPError("Failed to create embeddings", response)
            
            data = response.json()
            
            # Extract embeddings
            embeddings = [item["embedding"] for item in data["data"]]
            
            return EmbeddingResult(
                embeddings=embeddings,
                model=data.get("model", model),
                usage=data.get("usage", {}),
                texts=text_list
            )
    
    async def embed_batch(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        account_type: str = "individual"
    ) -> EmbeddingResult:
        """
        Create embeddings for a large batch of texts, processing in chunks.
        
        Args:
            texts: List of text strings to embed
            model: Embedding model to use
            batch_size: Number of texts to process per request
            account_type: GitHub account type
            
        Returns:
            EmbeddingResult with all embeddings combined
        """
        all_embeddings = []
        all_usage = {"prompt_tokens": 0, "total_tokens": 0}
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = await self.embed(batch, model, account_type)
            
            all_embeddings.extend(result.embeddings)
            all_usage["prompt_tokens"] += result.usage.get("prompt_tokens", 0)
            all_usage["total_tokens"] += result.usage.get("total_tokens", 0)
        
        return EmbeddingResult(
            embeddings=all_embeddings,
            model=model,
            usage=all_usage,
            texts=texts
        )
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        import math
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in embedding1))
        magnitude2 = math.sqrt(sum(b * b for b in embedding2))
        
        # Calculate cosine similarity
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def find_most_similar(
        self,
        query: str,
        texts: List[str],
        model: str = "text-embedding-3-small",
        top_k: int = 5
    ) -> List[tuple[str, float]]:
        """
        Find the most similar texts to a query.
        
        Args:
            query: Query text
            texts: List of texts to search
            model: Embedding model to use
            top_k: Number of most similar texts to return
            
        Returns:
            List of (text, similarity_score) tuples, sorted by similarity
        """
        # Get embeddings for query and all texts
        all_texts = [query] + texts
        result = await self.embed(all_texts, model)
        
        query_embedding = result.embeddings[0]
        text_embeddings = result.embeddings[1:]
        
        # Calculate similarities
        similarities = []
        for i, text_embedding in enumerate(text_embeddings):
            similarity = self.cosine_similarity(query_embedding, text_embedding)
            similarities.append((texts[i], similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# Convenience functions for quick usage
async def embed_text(text: str, model: str = "text-embedding-3-small", github_token: Optional[str] = None) -> List[float]:
    """
    Quick function to embed a single text.
    
    Args:
        text: Text to embed
        model: Embedding model to use
        github_token: GitHub token (optional)
        
    Returns:
        Embedding vector
    """
    client = CopilotEmbeddingClient(github_token)
    result = await client.embed(text, model)
    return result.embeddings[0]


async def embed_texts(texts: List[str], model: str = "text-embedding-3-small", github_token: Optional[str] = None) -> List[List[float]]:
    """
    Quick function to embed multiple texts.
    
    Args:
        texts: List of texts to embed
        model: Embedding model to use
        github_token: GitHub token (optional)
        
    Returns:
        List of embedding vectors
    """
    client = CopilotEmbeddingClient(github_token)
    result = await client.embed(texts, model)
    return result.embeddings


async def find_similar(query: str, texts: List[str], top_k: int = 5, model: str = "text-embedding-3-small") -> List[tuple[str, float]]:
    """
    Quick function to find similar texts.
    
    Args:
        query: Query text
        texts: List of texts to search
        top_k: Number of results to return
        model: Embedding model to use
        
    Returns:
        List of (text, similarity) tuples
    """
    client = CopilotEmbeddingClient()
    return await client.find_most_similar(query, texts, model, top_k)