"""FastAPI server implementation."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .routes.chat_completions import router as completions_router
from .routes.models import router as models_router
from .routes.embeddings import router as embeddings_router
from .routes.usage import router as usage_router
from .routes.token import router as token_router
from .routes.messages import router as messages_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Copilot API",
    description="GitHub Copilot to OpenAI/Anthropic API proxy",
    version="0.5.14"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Server running"}

# Mount routes
app.include_router(completions_router, prefix="/chat/completions")
app.include_router(models_router, prefix="/models")
app.include_router(embeddings_router, prefix="/embeddings")
app.include_router(usage_router, prefix="/usage")
app.include_router(token_router, prefix="/token")

# Compatibility with tools that expect v1/ prefix
app.include_router(completions_router, prefix="/v1/chat/completions")
app.include_router(models_router, prefix="/v1/models")
app.include_router(embeddings_router, prefix="/v1/embeddings")

# Anthropic compatible endpoints
app.include_router(messages_router, prefix="/v1/messages")

@app.post("/v1/messages/count_tokens")
async def count_tokens():
    """Simple token count endpoint for Anthropic compatibility."""
    return {"input_tokens": 1}