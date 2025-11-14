# Response ID Lifecycle - FAQ

## Do we need to manage the lifecycle of response_id?

**Short answer:** Yes, but it's relatively simple. Response IDs are temporary and expire after a short period (typically 5-60 minutes).

## Key Points

### 1. **Automatic Storage**
VSCode automatically stores response IDs in the conversation history as "opaque" content parts within assistant messages. You don't need to manually track them separately.

### 2. **Automatic Retrieval**
When making a new request, VSCode automatically:
- Searches backwards through conversation history
- Finds the most recent response_id for the current model
- Includes it as `previous_response_id` in the request
- Only sends messages that came after that response

### 3. **Server-Side Expiration**
The server invalidates response IDs when:

| Reason | Typical Timeframe |
|--------|-------------------|
| **Time-based expiration** | 5-60 minutes (varies by provider) |
| **Cache eviction** | When server is under high load |
| **Model changes** | Immediately when switching models |
| **Session changes** | When auth token changes |

### 4. **Error Handling**
When a response_id expires, the server returns:

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_stateful_marker",
    "message": "The provided response_id is invalid or has expired"
  }
}
```

VSCode has prepared (but not yet enabled) automatic retry logic that would:
1. Detect the `InvalidStatefulMarker` error
2. Retry the request without the `previous_response_id`
3. Send the full conversation history instead

## When to Clear Response IDs

### ✓ Always Clear When:
- Starting a new conversation
- Switching to a different model
- User authentication changes
- After receiving an `InvalidStatefulMarker` error

### ✓ Consider Clearing When:
- Idle for more than 5 minutes
- System prompt changes significantly
- Context window is getting full

### ✗ Don't Clear When:
- Making sequential requests in the same conversation
- Within a few minutes of the last request
- Same model and user session

## Best Practices

### 1. **Use Within Active Conversations**
```python
# ✓ Good: Sequential requests in active conversation
response1 = api.create_response(messages)
# ... user types follow-up immediately ...
response2 = api.create_response(
    new_messages,
    previous_response_id=response1.id  # Still valid
)
```

### 2. **Don't Persist Long-Term**
```python
# ❌ Bad: Storing for hours
cache = {"response_id": "resp_123", "saved_at": "2024-01-01 10:00"}
# ... hours later ...
use_response_id(cache["response_id"])  # Likely expired!

# ✓ Good: Clear on new session
def start_new_conversation():
    conversation.clear()
    response_ids.clear()
```

### 3. **Handle Expiration Gracefully**
```python
def make_request_with_fallback(messages, previous_response_id=None):
    try:
        return api.create_response(
            messages=messages,
            previous_response_id=previous_response_id
        )
    except InvalidStatefulMarkerError:
        # Fallback: resend full conversation
        return api.create_response(
            messages=full_conversation_history
        )
```

### 4. **Model-Specific IDs**
```python
# Each model has its own response_id namespace
response_ids = {
    "claude-3.5-sonnet": "resp_abc123",
    "gpt-4o": "resp_xyz789"
}

# Use the correct ID for the current model
current_id = response_ids.get(current_model)
```

## Testing Expiration

Use the provided test script to determine actual expiration times:

```bash
# Test with 5 minute delay
python test_response_id_expiration.py --delay 300

# Test with 10 minute delay
python test_response_id_expiration.py --delay 600

# Test Claude Sonnet
python test_response_id_expiration.py --model claude-3.5-sonnet --delay 300
```

## Expected Expiration Times

Based on industry standards and documentation:

| Provider | Model | Estimated TTL |
|----------|-------|---------------|
| **Anthropic** | Claude 3.5 Sonnet | ~5 minutes |
| **Anthropic** | Claude 3.7 Sonnet | ~5 minutes |
| **OpenAI** | GPT-4o | ~10-30 minutes (undocumented) |
| **OpenAI** | O1 models | ~10-30 minutes (undocumented) |
| **GitHub Copilot** | Varies by backend | Depends on provider |

**Note:** These are estimates. Actual expiration times may vary based on:
- Server load
- Cache pressure
- Provider-specific policies
- Geographic region

## Monitoring Cache Effectiveness

Track cache hit rates to ensure caching is working:

```python
def track_cache_usage(response):
    usage = response.usage
    cached = usage.input_tokens_details.cached_tokens
    total = usage.input_tokens

    if cached > 0:
        hit_rate = cached / total
        print(f"Cache hit rate: {hit_rate:.1%}")

        # Log metrics
        metrics.record("cache_hit_rate", hit_rate)
        metrics.record("cached_tokens", cached)
    else:
        metrics.record("cache_miss", 1)
```

## Summary

### Do You Need to Manage Lifecycle?

**Yes, but minimally:**

1. ✓ **Store** response_ids in conversation history (automatic in VSCode)
2. ✓ **Use** them for follow-up requests within minutes
3. ✓ **Clear** them when starting new conversations or switching models
4. ✓ **Handle** expiration errors gracefully with fallback
5. ✗ **Don't** persist them long-term or across sessions

### The Golden Rule

> **Use response_ids for sequential requests within the same conversation session (< 5 minutes apart). Clear them when the conversation context changes.**

## Additional Resources

- [RESPONSE_ID_LIFECYCLE.md](./RESPONSE_ID_LIFECYCLE.md) - Detailed lifecycle documentation
- [test_response_id_expiration.py](./test_response_id_expiration.py) - Expiration testing script
- [Anthropic Prompt Caching Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [OpenAI Responses API Docs](https://platform.openai.com/docs/api-reference/responses)
