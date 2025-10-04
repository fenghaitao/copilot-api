"""Basic functionality tests."""

import pytest
from fastapi.testclient import TestClient

from copilot_api.server import app
from copilot_api.lib.state import state


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Server running"}


def test_models_endpoint(client):
    """Test the models endpoint."""
    response = client.get("/models")
    assert response.status_code == 200
    # Should return empty list when no models cached
    data = response.json()
    assert "data" in data


def test_token_endpoint(client):
    """Test the token status endpoint."""
    response = client.get("/token")
    assert response.status_code == 200
    data = response.json()
    assert "has_github_token" in data
    assert "has_copilot_token" in data


def test_usage_endpoint(client):
    """Test the usage endpoint."""
    response = client.get("/usage")
    assert response.status_code == 200
    data = response.json()
    assert "usage" in data


def test_embeddings_endpoint(client):
    """Test the embeddings endpoint."""
    # Test with valid embedding request data
    embedding_request = {
        "input": "test text for embedding",
        "model": "text-embedding-ada-002"
    }
    response = client.post("/embeddings", json=embedding_request)
    
    # Since we don't have a real Copilot token in tests, we expect an error response
    # but it should be a proper error format, not a validation error
    assert response.status_code != 422  # Should not be a validation error
    
    if response.status_code != 200:
        # If it's an error response, check it has proper error format
        data = response.json()
        if "error" in data:
            assert "message" in data["error"]
            assert "type" in data["error"]


def test_anthropic_count_tokens(client):
    """Test Anthropic count tokens endpoint."""
    response = client.post("/v1/messages/count_tokens", json={})
    assert response.status_code == 200
    data = response.json()
    assert "input_tokens" in data