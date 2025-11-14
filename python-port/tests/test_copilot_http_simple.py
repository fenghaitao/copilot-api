#!/usr/bin/env python3
"""
Simple GitHub Copilot Responses API Validator (no LiteLLM required)

This script directly tests the GitHub Copilot Responses API to validate
prompt caching support for Claude Sonnet and other models.

Requirements:
    pip install requests

Usage:
    python validate_copilot_simple.py
    
This script reads the GitHub token from ~/.config/copilot-api/github_token
and exchanges it for a Copilot token using the copilot-api framework.
"""

import os
import sys
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests is not installed. Install it with: pip install requests")
    sys.exit(1)

# Add the src directory to Python path to import copilot_api
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from copilot_api.services.github.get_copilot_token import get_copilot_token
    from copilot_api.services.get_vscode_version import get_vscode_version
    from copilot_api.lib.state import State
except ImportError as e:
    print(f"Error: Failed to import copilot_api modules: {e}")
    print("Make sure you're running this from the python-port directory")
    sys.exit(1)


async def get_copilot_api_key() -> tuple[str, str]:
    """Get Copilot API key from GitHub token using copilot-api framework"""
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_API_KEY")
    
    if not github_token:
        config_path = os.path.expanduser("~/.config/copilot-api/github_token")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    github_token = f.read().strip()
            except Exception as e:
                print(f"Warning: Failed to read token from {config_path}: {e}")
    
    if not github_token:
        print("Error: GitHub token not found.")
        print("Please set GITHUB_TOKEN environment variable or")
        print("ensure token exists at: ~/.config/copilot-api/github_token")
        sys.exit(1)
    
    # Import state and set tokens
    from copilot_api.lib.state import state
    
    # Set GitHub token in state
    state.github_token = github_token
    state.vscode_version = await get_vscode_version()
    
    # Exchange GitHub token for Copilot token using the state-aware function
    try:
        result = await get_copilot_token()
        copilot_token = result["token"]
        return copilot_token, state.vscode_version
    except Exception as e:
        print(f"Error: Failed to get Copilot token: {e}")
        sys.exit(1)


def list_models(api_key: str, vscode_version: str) -> list:
    """List available GitHub Copilot models"""
    print("\n" + "="*80)
    print("FETCHING AVAILABLE MODELS")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "copilot-integration-id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    try:
        response = requests.get(
            "https://api.githubcopilot.com/models",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])

            print(f"\n✓ Found {len(models)} models\n")

            for model in models:
                model_id = model.get("id", "unknown")
                model_name = model.get("name", "unknown")
                family = model.get("capabilities", {}).get("family", "unknown")
                supported_endpoints = model.get("supported_endpoints", [])

                print(f"• {model_id}")
                print(f"  Name: {model_name}")
                print(f"  Family: {family}")

                if "/responses" in supported_endpoints:
                    print(f"  ✓ Supports Responses API (caching available)")
                elif "/chat/completions" in supported_endpoints:
                    print(f"  ⚠ Only Chat Completions API (no caching)")
                else:
                    print(f"  Endpoints: {', '.join(supported_endpoints)}")
                print()

            return models
        else:
            print(f"✗ Failed to fetch models: HTTP {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return []

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def test_responses_api(api_key: str, vscode_version: str, model: str) -> Dict[str, Any]:
    """Test Responses API with caching"""
    print("\n" + "="*80)
    print(f"TESTING RESPONSES API: {model}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "Editor-Version": "vscode/1.85.0",
        "Copilot-Integration-Id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    # Create a long system message that should be cached
    long_system_message = (
        "You are a helpful AI assistant. " +
        "This is a long system prompt designed to test prompt caching. " * 50
    )

    # First request
    payload1 = {
        "model": model,
        "input": [
            {"role": "system", "content": long_system_message},
            {"role": "user", "content": "Say 'Hello' in exactly one word."}
        ],
        "max_output_tokens": 20,
        "stream": False
    }

    print("\n→ Request 1: Initial request (no cache expected)")
    print(f"  System message length: {len(long_system_message)} chars")

    try:
        start1 = time.time()
        response1 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload1,
            timeout=30
        )
        elapsed1 = time.time() - start1

        if response1.status_code != 200:
            print(f"\n✗ Request failed: HTTP {response1.status_code}")
            print(f"Response: {response1.text[:500]}")
            return {"success": False, "error": response1.text[:500]}

        data1 = response1.json()
        response_id = data1.get("id")
        usage1 = data1.get("usage", {})

        input_tokens1 = usage1.get("input_tokens", 0)
        output_tokens1 = usage1.get("output_tokens", 0)
        cached_tokens1 = usage1.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"\n✓ Request 1 successful")
        print(f"  Response ID: {response_id}")
        print(f"  Input tokens: {input_tokens1}")
        print(f"  Output tokens: {output_tokens1}")
        print(f"  Cached tokens: {cached_tokens1}")
        print(f"  Time: {elapsed1:.2f}s")

        # Extract response text
        output1 = data1.get("output", [])
        if output1:
            first_output = output1[0]
            if first_output.get("type") == "message":
                content = first_output.get("content", [])
                if content and content[0].get("type") == "output_text":
                    print(f"  Response: {content[0].get('text', '')}")

        # Second request using previous_response_id
        payload2 = {
            "model": model,
            "previous_response_id": response_id,
            "input": [
                {"role": "user", "content": "Now say 'World' in exactly one word."}
            ],
            "max_output_tokens": 20,
            "stream": False
        }

        print("\n→ Request 2: Using previous_response_id (cache expected)")

        start2 = time.time()
        response2 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload2,
            timeout=30
        )
        elapsed2 = time.time() - start2

        if response2.status_code != 200:
            print(f"\n✗ Request 2 failed: HTTP {response2.status_code}")
            print(f"Response: {response2.text[:500]}")
            return {
                "success": True,
                "request1": {"cached_tokens": cached_tokens1, "time": elapsed1},
                "request2": {"success": False, "error": response2.text[:500]}
            }

        data2 = response2.json()
        usage2 = data2.get("usage", {})

        input_tokens2 = usage2.get("input_tokens", 0)
        output_tokens2 = usage2.get("output_tokens", 0)
        cached_tokens2 = usage2.get("input_tokens_details", {}).get("cached_tokens", 0)

        print(f"\n✓ Request 2 successful")
        print(f"  Response ID: {data2.get('id')}")
        print(f"  Input tokens: {input_tokens2}")
        print(f"  Output tokens: {output_tokens2}")
        print(f"  Cached tokens: {cached_tokens2}")
        print(f"  Time: {elapsed2:.2f}s")

        # Extract response text
        output2 = data2.get("output", [])
        if output2:
            first_output = output2[0]
            if first_output.get("type") == "message":
                content = first_output.get("content", [])
                if content and content[0].get("type") == "output_text":
                    print(f"  Response: {content[0].get('text', '')}")

        # Analyze caching
        print("\n" + "-"*80)
        print("CACHING ANALYSIS")
        print("-"*80)

        if cached_tokens2 > 0:
            print(f"✓✓ PROMPT CACHING IS WORKING!")
            print(f"   {cached_tokens2} tokens were served from cache")
            print(f"   Time saved: {elapsed1 - elapsed2:.2f}s ({((elapsed1 - elapsed2) / elapsed1 * 100):.1f}%)")
            cache_status = "WORKING"
        else:
            print(f"⚠ No cached tokens detected")
            print(f"  This could mean:")
            print(f"  - Model doesn't support caching")
            print(f"  - Cache hasn't been populated yet")
            print(f"  - previous_response_id not working as expected")
            cache_status = "NOT_DETECTED"

        return {
            "success": True,
            "model": model,
            "cache_status": cache_status,
            "request1": {
                "input_tokens": input_tokens1,
                "output_tokens": output_tokens1,
                "cached_tokens": cached_tokens1,
                "time": elapsed1
            },
            "request2": {
                "input_tokens": input_tokens2,
                "output_tokens": output_tokens2,
                "cached_tokens": cached_tokens2,
                "time": elapsed2
            }
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {"success": False, "error": str(e)}


def test_chat_completions_api(api_key: str, vscode_version: str, model: str) -> Dict[str, Any]:
    """Test Chat Completions API (for comparison)"""
    print("\n" + "="*80)
    print(f"TESTING CHAT COMPLETIONS API: {model}")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01",
        "Editor-Version": "vscode/1.85.0",
        "Copilot-Integration-Id": "vscode-chat",
        "editor-version": f"vscode/{vscode_version}",
        "editor-plugin-version": "copilot-chat/0.26.7",
        "user-agent": "GitHubCopilotChat/0.26.7",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Chat Completions' in exactly 4 words."}
        ],
        "max_tokens": 20,
        "temperature": 0.7
    }

    try:
        start = time.time()
        response = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start

        if response.status_code != 200:
            print(f"\n✗ Request failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return {"success": False, "error": response.text[:500]}

        data = response.json()
        usage = data.get("usage", {})

        print(f"\n✓ Request successful")
        print(f"  Model: {data.get('model')}")
        print(f"  Prompt tokens: {usage.get('prompt_tokens', 0)}")
        print(f"  Completion tokens: {usage.get('completion_tokens', 0)}")
        print(f"  Total tokens: {usage.get('total_tokens', 0)}")
        print(f"  Time: {elapsed:.2f}s")

        choices = data.get("choices", [])
        if choices:
            print(f"  Response: {choices[0].get('message', {}).get('content', '')}")

        return {"success": True, "usage": usage, "time": elapsed}

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {"success": False, "error": str(e)}


async def async_main():
    """Main async function"""
    print("\n" + "="*80)
    print("GITHUB COPILOT RESPONSES API VALIDATOR")
    print("Simple version - Direct API calls only")
    print("="*80)

    # Get Copilot API key from GitHub token
    copilot_token, vscode_version = await get_copilot_api_key()
    print(f"\n✓ Successfully obtained Copilot token")
    print(f"  VS Code version: {vscode_version}")

    # List available models
    models = list_models(copilot_token, vscode_version)

    # Test only gpt-5-mini model
    test_models = ["gpt-5-mini"]

    print("\n" + "="*80)
    print("TESTING MODELS")
    print("="*80)

    results = {}

    for model in test_models:
        print(f"\n{'='*80}")
        print(f"MODEL: {model}")
        print('='*80)

        # Test Chat Completions API
        chat_result = test_chat_completions_api(copilot_token, vscode_version, model)

        # Test Responses API
        responses_result = test_responses_api(copilot_token, vscode_version, model)

        results[model] = {
            "chat_completions": chat_result,
            "responses_api": responses_result
        }

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    for model, result in results.items():
        print(f"{model}:")

        # Chat Completions
        if result["chat_completions"].get("success"):
            print(f"  ✓ Chat Completions API: Working")
        else:
            print(f"  ✗ Chat Completions API: Failed")

        # Responses API
        if result["responses_api"].get("success"):
            print(f"  ✓ Responses API: Working")

            cache_status = result["responses_api"].get("cache_status")
            if cache_status == "WORKING":
                cached = result["responses_api"]["request2"]["cached_tokens"]
                print(f"    ✓✓ Prompt Caching: WORKING ({cached} tokens)")
            else:
                print(f"    ⚠ Prompt Caching: Not detected")
        else:
            print(f"  ✗ Responses API: Failed")

        print()

    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80 + "\n")


def main():
    """Main function wrapper"""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
