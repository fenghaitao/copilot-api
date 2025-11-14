#!/usr/bin/env python3
"""
Validate GitHub Copilot Responses API with LiteLLM

This script tests whether GitHub Copilot models support
the Responses API and prompt caching through LiteLLM.

Requirements:
    pip install litellm requests

Usage:
    python validate_copilot_responses_api.py
    
This script reads the GitHub token from ~/.config/copilot-api/github_token
and exchanges it for a Copilot token using the copilot-api framework.
"""

import os
import sys
import json
from typing import Optional, Dict, Any
import time
from pathlib import Path

try:
    import litellm
    from litellm import completion, responses
except ImportError:
    print("Error: litellm is not installed. Install it with: pip install litellm")
    sys.exit(1)

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
    from copilot_api.lib.state import state
except ImportError as e:
    print(f"Error: Failed to import copilot_api modules: {e}")
    print("Make sure you're running this from the python-port directory")
    sys.exit(1)


class CopilotResponsesAPIValidator:
    """Validator for GitHub Copilot Responses API"""

    def __init__(self, copilot_token: str, vscode_version: str):
        """
        Initialize the validator

        Args:
            copilot_token: GitHub Copilot API token
            vscode_version: VS Code version string
        """
        self.api_key = copilot_token
        self.vscode_version = vscode_version

        # Configure LiteLLM
        litellm.set_verbose = False

    def list_available_models(self) -> list:
        """
        List available GitHub Copilot models

        Returns:
            List of model information dictionaries
        """
        print("\n" + "="*80)
        print("FETCHING AVAILABLE MODELS")
        print("="*80)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "X-GitHub-Api-Version": "2025-04-01",
            "user-agent": "GitHubCopilotChat/0.26.7",
            "Editor-Version": "vscode/1.85.0",
            "Copilot-Integration-Id": "vscode-chat",
        }

        try:
            # Try to fetch models from GitHub Copilot API
            response = requests.get(
                "https://api.githubcopilot.com/models",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])

                print(f"\n✓ Found {len(models)} models")
                print("\nAvailable models:")
                for model in models:
                    model_id = model.get("id", "unknown")
                    model_name = model.get("name", "unknown")
                    family = model.get("capabilities", {}).get("family", "unknown")
                    supported_endpoints = model.get("supported_endpoints", [])

                    print(f"\n  • {model_id}")
                    print(f"    Name: {model_name}")
                    print(f"    Family: {family}")
                    print(f"    Supported Endpoints: {', '.join(supported_endpoints) if supported_endpoints else 'N/A'}")

                    # Check if Responses API is supported
                    if "/responses" in supported_endpoints:
                        print(f"    ✓ Supports Responses API (caching available)")
                    elif "/chat/completions" in supported_endpoints:
                        print(f"    ⚠ Only supports Chat Completions API (no caching)")

                return models
            else:
                print(f"\n✗ Failed to fetch models: HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"\n✗ Error fetching models: {e}")
            return []

    def test_chat_completions_api(self, model: str = "gpt-4o") -> Dict[str, Any]:
        """
        Test the Chat Completions API

        Args:
            model: Model identifier

        Returns:
            Dictionary with test results
        """
        print("\n" + "="*80)
        print(f"TESTING CHAT COMPLETIONS API: {model}")
        print("="*80)

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Chat Completions API' in exactly 5 words."}
        ]

        try:
            start_time = time.time()

            response = completion(
                model=f"github/{model}",
                messages=messages,
                api_key=self.api_key,
                api_base="https://api.githubcopilot.com",
                max_tokens=50,
                temperature=0.7,
                extra_headers={
                    "Editor-Version": "vscode/1.85.0",
                    "Copilot-Integration-Id": "vscode-chat",
                    "editor-version": f"vscode/{self.vscode_version}",
                    "editor-plugin-version": "copilot-chat/0.26.7",
                    "user-agent": "GitHubCopilotChat/0.26.7",
                }
            )

            elapsed = time.time() - start_time

            result = {
                "success": True,
                "model": response.model,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cached_tokens": getattr(getattr(response.usage, "prompt_tokens_details", None), "cached_tokens", 0) if hasattr(response.usage, "prompt_tokens_details") else 0
                },
                "elapsed_time": elapsed
            }

            print(f"\n✓ Request successful")
            print(f"  Model: {result['model']}")
            print(f"  Response: {result['content'][:100]}...")
            print(f"  Tokens: {result['usage']['prompt_tokens']} prompt + {result['usage']['completion_tokens']} completion = {result['usage']['total_tokens']} total")
            print(f"  Cached tokens: {result['usage']['cached_tokens']}")
            print(f"  Time: {elapsed:.2f}s")

            return result

        except Exception as e:
            print(f"\n✗ Request failed: {e}")
            return {"success": False, "error": str(e)}

    def test_responses_api(self, model: str = "gpt-4o") -> Dict[str, Any]:
        """
        Test the Responses API (with caching support) using LiteLLM

        Args:
            model: Model identifier

        Returns:
            Dictionary with test results
        """
        print("\n" + "="*80)
        print(f"TESTING RESPONSES API: {model}")
        print("="*80)

        # First request - should not have cached tokens
        input_messages = [
            {"role": "system", "content": "You are a helpful assistant. This is a long system prompt that should be cached for subsequent requests. " * 10},
            {"role": "user", "content": "Say 'Hello from Responses API' in exactly 5 words."}
        ]

        try:
            print("\n→ Making first request (no cache expected)...")
            start_time = time.time()

            # Use LiteLLM responses API with GitHub Copilot
            response = responses(
                model=model,
                input=input_messages,
                custom_llm_provider="github_copilot",
                max_output_tokens=50,
                extra_headers={
                    "Editor-Version": "vscode/1.85.0",
                    "Copilot-Integration-Id": "vscode-chat",
                    "editor-version": f"vscode/{self.vscode_version}",
                    "editor-plugin-version": "copilot-chat/0.26.7",
                    "user-agent": "GitHubCopilotChat/0.26.7",
                }
            )

            elapsed = time.time() - start_time

            result = {
                "success": True,
                "response_id": response.id,
                "model": response.model,
                "output": response.output,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cached_tokens": getattr(getattr(response.usage, "input_tokens_details", None), "cached_tokens", 0) if hasattr(response.usage, "input_tokens_details") else 0
                },
                "elapsed_time": elapsed
            }

            cached_tokens = result["usage"]["cached_tokens"]

            print(f"\n✓ First request successful")
            print(f"  Response ID: {result['response_id']}")
            print(f"  Model: {result['model']}")
            print(f"  Output items: {len(result['output'])}")
            print(f"  Tokens: {result['usage']['input_tokens']} input + {result['usage']['output_tokens']} output = {result['usage']['total_tokens']} total")
            print(f"  Cached tokens: {cached_tokens}")
            print(f"  Time: {elapsed:.2f}s")

            # Second request with previous_response_id - should use cache
            print("\n→ Making second request (cache expected)...")
            second_input = [
                {"role": "user", "content": "Now say 'Cached response works' in exactly 3 words."}
            ]

            start_time = time.time()
            response2 = responses(
                model=model,
                input=second_input,
                custom_llm_provider="github_copilot",
                max_output_tokens=50,
                previous_response_id=result["response_id"],
                extra_headers={
                    "Editor-Version": "vscode/1.85.0",
                    "Copilot-Integration-Id": "vscode-chat",
                    "editor-version": f"vscode/{self.vscode_version}",
                    "editor-plugin-version": "copilot-chat/0.26.7",
                    "user-agent": "GitHubCopilotChat/0.26.7",
                }
            )
            elapsed2 = time.time() - start_time

            cached_tokens2 = getattr(getattr(response2.usage, "input_tokens_details", None), "cached_tokens", 0) if hasattr(response2.usage, "input_tokens_details") else 0

            print(f"\n✓ Second request successful")
            print(f"  Response ID: {response2.id}")
            print(f"  Tokens: {response2.usage.input_tokens} input + {response2.usage.output_tokens} output")
            print(f"  Cached tokens: {cached_tokens2}")
            print(f"  Time: {elapsed2:.2f}s")

            if cached_tokens2 > 0:
                print(f"\n  ✓✓ CACHING WORKS! {cached_tokens2} tokens were served from cache")
            else:
                print(f"\n  ⚠ No cached tokens detected (may not be supported for this model)")

            result["second_request"] = {
                "cached_tokens": cached_tokens2,
                "elapsed_time": elapsed2
            }

            return result

        except Exception as e:
            print(f"\n✗ Request failed: {e}")
            return {"success": False, "error": str(e)}

    def validate_model(self, model: str) -> Dict[str, Any]:
        """
        Validate a specific model's API support

        Args:
            model: Model identifier (e.g., 'gpt-4o', 'claude-3.5-sonnet')

        Returns:
            Dictionary with validation results
        """
        print("\n" + "="*80)
        print(f"VALIDATING MODEL: {model}")
        print("="*80)

        results = {
            "model": model,
            "chat_completions": None,
            "responses_api": None
        }

        # Test Chat Completions API
        results["chat_completions"] = self.test_chat_completions_api(model)

        # Test Responses API
        results["responses_api"] = self.test_responses_api(model)

        return results


async def async_main():
    """Main async function"""
    print("\n" + "="*80)
    print("GITHUB COPILOT RESPONSES API VALIDATOR")
    print("="*80)

    # Get Copilot token
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_API_KEY")
    
    if not github_token:
        config_path = os.path.expanduser("~/.config/copilot-api/github_token")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    github_token = f.read().strip()
            except Exception as e:
                print(f"✗ Failed to read token from {config_path}: {e}")
                sys.exit(1)
    
    if not github_token:
        print("✗ GitHub token not found.")
        print("Please set GITHUB_TOKEN environment variable or")
        print("ensure token exists at: ~/.config/copilot-api/github_token")
        sys.exit(1)
    
    # Set up state and get Copilot token
    state.github_token = github_token
    state.vscode_version = await get_vscode_version()
    
    try:
        result = await get_copilot_token()
        copilot_token = result["token"]
        print(f"\n✓ Successfully obtained Copilot token")
        print(f"  VS Code version: {state.vscode_version}")
    except Exception as e:
        print(f"\n✗ Failed to get Copilot token: {e}")
        sys.exit(1)

    # Initialize validator
    try:
        validator = CopilotResponsesAPIValidator(copilot_token, state.vscode_version)
    except Exception as e:
        print(f"\n✗ {e}")
        sys.exit(1)

    # List available models
    models = validator.list_available_models()

    # Test only gpt-5-mini model
    test_models = ["gpt-5-mini"]

    print("\n" + "="*80)
    print("TESTING MODELS")
    print("="*80)

    results = {}
    for model in test_models:
        try:
            results[model] = validator.validate_model(model)
        except Exception as e:
            print(f"\n✗ Error testing {model}: {e}")
            results[model] = {"error": str(e)}

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    for model, result in results.items():
        print(f"\n{model}:")

        if "error" in result:
            print(f"  ✗ Error: {result['error']}")
            continue

        # Chat Completions API
        if result.get("chat_completions", {}).get("success"):
            print(f"  ✓ Chat Completions API: Working")
        else:
            print(f"  ✗ Chat Completions API: Failed")

        # Responses API
        if result.get("responses_api", {}).get("success"):
            print(f"  ✓ Responses API: Working")

            # Check caching
            second_req = result["responses_api"].get("second_request", {})
            cached = second_req.get("cached_tokens", 0)
            if cached > 0:
                print(f"    ✓✓ Prompt Caching: WORKING ({cached} tokens cached)")
            else:
                print(f"    ⚠ Prompt Caching: Not detected")
        else:
            print(f"  ✗ Responses API: Failed")

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80 + "\n")


def main():
    """Main function wrapper"""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
