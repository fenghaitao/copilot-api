#!/usr/bin/env python3
"""
Validate GitHub Copilot Responses API with LiteLLM

This script tests whether GitHub Copilot models (including Claude Sonnet) support
the Responses API and prompt caching through LiteLLM.

Requirements:
    pip install litellm requests

Usage:
    python validate_copilot_responses_api.py
"""

import os
import sys
import json
from typing import Optional, Dict, Any
import time

try:
    import litellm
    from litellm import completion
except ImportError:
    print("Error: litellm is not installed. Install it with: pip install litellm")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests is not installed. Install it with: pip install requests")
    sys.exit(1)


class CopilotResponsesAPIValidator:
    """Validator for GitHub Copilot Responses API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the validator

        Args:
            api_key: GitHub Copilot API key. If not provided, will try to read from
                    GITHUB_TOKEN or COPILOT_API_KEY environment variables
        """
        self.api_key = api_key or os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GitHub API key not found. Please provide it via:\n"
                "  1. Constructor parameter\n"
                "  2. GITHUB_TOKEN environment variable\n"
                "  3. COPILOT_API_KEY environment variable"
            )

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
            "X-GitHub-Api-Version": "2025-05-01"
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
                temperature=0.7
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
                    "cached_tokens": getattr(response.usage, "prompt_tokens_details", {}).get("cached_tokens", 0) if hasattr(response.usage, "prompt_tokens_details") else 0
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
        Test the Responses API (with caching support)

        Args:
            model: Model identifier

        Returns:
            Dictionary with test results
        """
        print("\n" + "="*80)
        print(f"TESTING RESPONSES API: {model}")
        print("="*80)

        # Responses API uses a different format
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2025-05-01"
        }

        # First request - should not have cached tokens
        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": "You are a helpful assistant. This is a long system prompt that should be cached for subsequent requests. " * 10},
                {"role": "user", "content": "Say 'Hello from Responses API' in exactly 5 words."}
            ],
            "max_output_tokens": 50,
            "temperature": 0.7,
            "stream": False
        }

        try:
            print("\n→ Making first request (no cache expected)...")
            start_time = time.time()

            response = requests.post(
                "https://api.githubcopilot.com/responses",
                headers=headers,
                json=payload,
                timeout=30
            )

            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                result = {
                    "success": True,
                    "response_id": data.get("id"),
                    "model": data.get("model"),
                    "output": data.get("output", []),
                    "usage": data.get("usage", {}),
                    "elapsed_time": elapsed
                }

                cached_tokens = result["usage"].get("input_tokens_details", {}).get("cached_tokens", 0)

                print(f"\n✓ First request successful")
                print(f"  Response ID: {result['response_id']}")
                print(f"  Model: {result['model']}")
                print(f"  Output items: {len(result['output'])}")
                print(f"  Tokens: {result['usage'].get('input_tokens', 0)} input + {result['usage'].get('output_tokens', 0)} output = {result['usage'].get('total_tokens', 0)} total")
                print(f"  Cached tokens: {cached_tokens}")
                print(f"  Time: {elapsed:.2f}s")

                # Second request with previous_response_id - should use cache
                print("\n→ Making second request (cache expected)...")
                payload["previous_response_id"] = result["response_id"]
                payload["input"] = [
                    {"role": "user", "content": "Now say 'Cached response works' in exactly 3 words."}
                ]

                start_time = time.time()
                response2 = requests.post(
                    "https://api.githubcopilot.com/responses",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                elapsed2 = time.time() - start_time

                if response2.status_code == 200:
                    data2 = response2.json()
                    cached_tokens2 = data2.get("usage", {}).get("input_tokens_details", {}).get("cached_tokens", 0)

                    print(f"\n✓ Second request successful")
                    print(f"  Response ID: {data2.get('id')}")
                    print(f"  Tokens: {data2.get('usage', {}).get('input_tokens', 0)} input + {data2.get('usage', {}).get('output_tokens', 0)} output")
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
                else:
                    print(f"\n✗ Second request failed: HTTP {response2.status_code}")
                    print(f"  Response: {response2.text[:200]}")

                return result
            else:
                print(f"\n✗ Request failed: HTTP {response.status_code}")
                print(f"  Response: {response.text[:500]}")
                return {"success": False, "error": f"HTTP {response.status_code}", "response": response.text[:500]}

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


def main():
    """Main function"""
    print("\n" + "="*80)
    print("GITHUB COPILOT RESPONSES API VALIDATOR")
    print("="*80)

    # Initialize validator
    try:
        validator = CopilotResponsesAPIValidator()
    except ValueError as e:
        print(f"\n✗ {e}")
        sys.exit(1)

    # List available models
    models = validator.list_available_models()

    # Test specific models
    test_models = [
        "gpt-4o",
        "claude-3.5-sonnet",
        "claude-3.7-sonnet"
    ]

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


if __name__ == "__main__":
    main()
