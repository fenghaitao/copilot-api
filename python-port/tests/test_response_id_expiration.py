#!/usr/bin/env python3
"""
Test Response ID Expiration for GitHub Copilot Responses API

This script tests how long response_ids remain valid by making requests
with delays between them.

Requirements:
    pip install requests

Usage:
    export GITHUB_TOKEN="your_github_token"

    # Test with 5 minute delay
    python test_response_id_expiration.py --delay 300

    # Test with 10 minute delay
    python test_response_id_expiration.py --delay 600

    # Test specific model
    python test_response_id_expiration.py --model claude-3.5-sonnet --delay 300
"""

import os
import sys
import time
import argparse
from typing import Dict, Any

try:
    import requests
except ImportError:
    print("Error: requests is not installed. Install it with: pip install requests")
    sys.exit(1)


def get_api_key() -> str:
    """Get GitHub API key from environment"""
    api_key = os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_API_KEY")
    if not api_key:
        print("Error: GitHub API key not found.")
        print("Please set: export GITHUB_TOKEN='your_token'")
        sys.exit(1)
    return api_key


def test_response_id_expiration(
    api_key: str,
    model: str,
    delay_seconds: int
) -> Dict[str, Any]:
    """
    Test response_id expiration by waiting between requests

    Args:
        api_key: GitHub API key
        model: Model to test
        delay_seconds: How long to wait between requests

    Returns:
        Dictionary with test results
    """
    print("\n" + "="*80)
    print(f"TESTING RESPONSE_ID EXPIRATION")
    print("="*80)
    print(f"Model: {model}")
    print(f"Delay: {delay_seconds} seconds ({delay_seconds/60:.1f} minutes)")
    print("="*80)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2025-05-01"
    }

    # Create a long system message for better cache testing
    long_system = (
        "You are a helpful AI assistant. " +
        "This is a long system prompt designed to test prompt caching. " * 50
    )

    # First request
    payload1 = {
        "model": model,
        "input": [
            {"role": "system", "content": long_system},
            {"role": "user", "content": "Say 'First' in exactly one word."}
        ],
        "max_output_tokens": 10,
        "stream": False
    }

    print("\n" + "-"*80)
    print("STEP 1: Initial Request")
    print("-"*80)

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
            print(f"\n✗ Initial request failed: HTTP {response1.status_code}")
            print(f"Response: {response1.text[:500]}")
            return {
                "success": False,
                "step": "initial_request",
                "error": response1.text[:500]
            }

        data1 = response1.json()
        response_id = data1.get("id")
        usage1 = data1.get("usage", {})

        print(f"\n✓ Initial request successful")
        print(f"  Response ID: {response_id}")
        print(f"  Input tokens: {usage1.get('input_tokens', 0)}")
        print(f"  Output tokens: {usage1.get('output_tokens', 0)}")
        print(f"  Time: {elapsed1:.2f}s")

        # Extract response
        output1 = data1.get("output", [])
        if output1 and output1[0].get("type") == "message":
            content = output1[0].get("content", [])
            if content and content[0].get("type") == "output_text":
                print(f"  Response: {content[0].get('text', '')}")

        # Wait for potential expiration
        print("\n" + "-"*80)
        print(f"STEP 2: Waiting {delay_seconds} seconds...")
        print("-"*80)

        # Show countdown for long waits
        if delay_seconds >= 60:
            for remaining in range(delay_seconds, 0, -30):
                mins = remaining // 60
                secs = remaining % 60
                print(f"  ⏳ {mins}m {secs}s remaining...", end="\r")
                time.sleep(min(30, remaining))
            print(" " * 50, end="\r")  # Clear the line
        else:
            time.sleep(delay_seconds)

        print(f"✓ Wait complete ({delay_seconds}s elapsed)")

        # Second request using the old response_id
        payload2 = {
            "model": model,
            "previous_response_id": response_id,
            "input": [
                {"role": "user", "content": "Say 'Second' in exactly one word."}
            ],
            "max_output_tokens": 10,
            "stream": False
        }

        print("\n" + "-"*80)
        print(f"STEP 3: Request with {delay_seconds}s old response_id")
        print("-"*80)
        print(f"  Using response_id: {response_id}")

        start2 = time.time()
        response2 = requests.post(
            "https://api.githubcopilot.com/responses",
            headers=headers,
            json=payload2,
            timeout=30
        )
        elapsed2 = time.time() - start2

        # Analyze the response
        if response2.status_code == 200:
            data2 = response2.json()
            usage2 = data2.get("usage", {})
            cached_tokens = usage2.get("input_tokens_details", {}).get("cached_tokens", 0)

            print(f"\n✓✓ REQUEST SUCCESSFUL - Response ID still valid!")
            print(f"  Response ID: {data2.get('id')}")
            print(f"  Input tokens: {usage2.get('input_tokens', 0)}")
            print(f"  Cached tokens: {cached_tokens}")
            print(f"  Time: {elapsed2:.2f}s")

            # Extract response
            output2 = data2.get("output", [])
            if output2 and output2[0].get("type") == "message":
                content = output2[0].get("content", [])
                if content and content[0].get("type") == "output_text":
                    print(f"  Response: {content[0].get('text', '')}")

            print(f"\n" + "="*80)
            print("RESULT: Response IDs last at least {:.1f} minutes".format(delay_seconds/60))
            print("="*80)

            if cached_tokens > 0:
                print(f"✓ Caching is working ({cached_tokens} tokens from cache)")
            else:
                print(f"⚠ No cached tokens (caching may not be supported)")

            return {
                "success": True,
                "expired": False,
                "delay_seconds": delay_seconds,
                "delay_minutes": delay_seconds / 60,
                "response_id": response_id,
                "cached_tokens": cached_tokens,
                "time_saved": elapsed1 - elapsed2
            }

        elif response2.status_code == 400:
            error_data = response2.json()
            error_obj = error_data.get("error", {})
            error_code = error_obj.get("code", "")
            error_message = error_obj.get("message", "")

            print(f"\n✗ Request failed: HTTP 400")
            print(f"  Error code: {error_code}")
            print(f"  Error message: {error_message}")

            # Check if it's an expiration error
            is_expiration = (
                "invalid" in error_code.lower() or
                "expired" in error_code.lower() or
                "stateful" in error_code.lower()
            )

            if is_expiration:
                print(f"\n" + "="*80)
                print("RESULT: Response ID EXPIRED")
                print("="*80)
                print(f"✓ Response IDs expire before {delay_seconds/60:.1f} minutes")
                print(f"  Error indicates: {error_code}")

                return {
                    "success": True,
                    "expired": True,
                    "delay_seconds": delay_seconds,
                    "delay_minutes": delay_seconds / 60,
                    "response_id": response_id,
                    "error_code": error_code,
                    "error_message": error_message
                }
            else:
                print(f"\n⚠ Unexpected error (not expiration-related)")
                return {
                    "success": False,
                    "step": "second_request",
                    "error": error_data
                }

        else:
            print(f"\n✗ Request failed: HTTP {response2.status_code}")
            print(f"Response: {response2.text[:500]}")
            return {
                "success": False,
                "step": "second_request",
                "error": response2.text[:500]
            }

    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        return {"success": False, "error": "Interrupted by user"}

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Test GitHub Copilot response_id expiration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 5 minute delay
  python test_response_id_expiration.py --delay 300

  # Test with 10 minute delay
  python test_response_id_expiration.py --delay 600

  # Test Claude Sonnet with 5 minute delay
  python test_response_id_expiration.py --model claude-3.5-sonnet --delay 300

  # Quick test (30 seconds)
  python test_response_id_expiration.py --delay 30
        """
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="Model to test (default: gpt-4o)"
    )

    parser.add_argument(
        "--delay",
        type=int,
        default=300,
        help="Delay in seconds between requests (default: 300 = 5 minutes)"
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("GITHUB COPILOT RESPONSE_ID EXPIRATION TESTER")
    print("="*80)

    # Get API key
    api_key = get_api_key()

    # Run the test
    result = test_response_id_expiration(api_key, args.model, args.delay)

    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    if result.get("success"):
        if result.get("expired"):
            print(f"\n✓ Test completed successfully")
            print(f"  Model: {args.model}")
            print(f"  Result: Response IDs EXPIRE before {result['delay_minutes']:.1f} minutes")
            print(f"  Error code: {result.get('error_code')}")
            print(f"\n  Recommendation: Use response_ids within {result['delay_minutes']:.1f} minutes")
        else:
            print(f"\n✓ Test completed successfully")
            print(f"  Model: {args.model}")
            print(f"  Result: Response IDs last AT LEAST {result['delay_minutes']:.1f} minutes")
            print(f"  Cached tokens: {result.get('cached_tokens', 0)}")
            print(f"  Time saved: {result.get('time_saved', 0):.2f}s")
            print(f"\n  Recommendation: Response IDs are safe to use for at least {result['delay_minutes']:.1f} minutes")
            print(f"                  Try a longer delay to find the actual expiration time")
    else:
        print(f"\n✗ Test failed")
        print(f"  Step: {result.get('step', 'unknown')}")
        print(f"  Error: {result.get('error', 'unknown')}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
