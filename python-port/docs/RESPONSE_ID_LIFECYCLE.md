# Response ID Lifecycle Management

## Overview

The `response_id` (also called `stateful_marker` in VSCode's implementation) is used by the Responses API to enable prompt caching. Understanding its lifecycle is crucial for efficient API usage.

## How VSCode Manages Response IDs

### Storage in Conversation History

VSCode stores the `response_id` as an **opaque content part** in the assistant's message within the conversation history:

```typescript
// Stored in the assistant message content
{
  role: "assistant",
  content: [
    { type: "text", text: "Response text..." },
    { type: "opaque", value: {
      type: "stateful_marker",
      value: { modelId: "claude-3.5-sonnet", marker: "resp_abc123" }
    }}
  ]
}
```

### Retrieval Logic

When making a new request, VSCode:

1. **Searches backwards** through the conversation history
2. **Finds the most recent** stateful marker for the current model
3. **Slices the messages** to only send messages after that marker
4. **Includes `previous_response_id`** in the request

```typescript
function rawMessagesToResponseAPI(modelId: string, messages: readonly Raw.ChatMessage[], ignoreStatefulMarker: boolean) {
  const statefulMarkerAndIndex = !ignoreStatefulMarker && getStatefulMarkerAndIndex(modelId, messages);
  let previousResponseId: string | undefined;

  if (statefulMarkerAndIndex) {
    previousResponseId = statefulMarkerAndIndex.statefulMarker;
    messages = messages.slice(statefulMarkerAndIndex.index + 1); // Only send new messages
  }

  return { input: messages, previous_response_id: previousResponseId };
}
```

## Server-Side Invalidation

### When Response IDs Expire

Based on the code analysis and industry standards, response IDs are invalidated when:

#### 1. **Time-Based Expiration**
- **Typical TTL**: 5-60 minutes (varies by provider)
- **Anthropic Claude**: ~5 minutes (based on their prompt caching docs)
- **OpenAI**: Not publicly documented, likely 10-30 minutes
- **GitHub Copilot**: Depends on the underlying model provider

#### 2. **Cache Eviction**
- Server runs out of cache space
- Least Recently Used (LRU) eviction policy
- High load on the API

#### 3. **Model Changes**
- Switching to a different model
- Model version updates
- Different deployment/region

#### 4. **Session Invalidation**
- User authentication changes
- API key rotation
- Service restarts

### Error Response

When a `response_id` is invalid or expired, the server returns an error:

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_stateful_marker",
    "message": "The provided response_id is invalid or has expired"
  }
}
```

VSCode defines this error type:

```typescript
export enum ChatFetchResponseType {
  // ... other types
  InvalidStatefulMarker = 'invalid_stateful_marker',
}

// Error message shown to user:
case ChatFetchResponseType.InvalidStatefulMarker:
  return { message: l10n.t(`Your chat session state is invalid, please start a new chat.`) };
```

## Retry Strategy

### Current Implementation (Commented Out)

VSCode has **prepared but not enabled** automatic retry logic:

```typescript
public async makeChatRequest2(options: IMakeChatRequestOptions, token: CancellationToken): Promise<ChatResponse> {
  return this._makeChatRequest2({ ...options, ignoreStatefulMarker: options.ignoreStatefulMarker ?? true }, token);

  // Stateful responses API not supported for now
  // const response = await this._makeChatRequest2(options, token);
  // if (response.type === ChatFetchResponseType.InvalidStatefulMarker) {
  //   return this._makeChatRequest2({ ...options, ignoreStatefulMarker: true }, token);
  // }
  // return response;
}
```

### Why It's Disabled

The comment "Stateful responses API not supported for now" suggests:
- Feature is still being tested
- Waiting for broader model support
- Potential issues with the retry mechanism

### Recommended Retry Strategy

When implementing your own client:

```python
def make_request_with_retry(messages, previous_response_id=None, max_retries=1):
    """Make a request with automatic retry on invalid response_id"""

    for attempt in range(max_retries + 1):
        try:
            response = api.create_response(
                messages=messages,
                previous_response_id=previous_response_id if attempt == 0 else None
            )
            return response

        except InvalidStatefulMarkerError:
            if attempt < max_retries:
                print(f"Response ID expired, retrying without cache...")
                previous_response_id = None  # Clear the expired ID
                continue
            raise
```

## Best Practices

### 1. **Don't Rely on Long-Term Caching**
```python
# ❌ Bad: Storing response_id for hours
cache = {"response_id": "resp_123", "timestamp": time.time()}
# ... hours later ...
use_cached_id(cache["response_id"])  # Likely expired!

# ✓ Good: Use within the same conversation session
response1 = make_request(messages)
response_id = response1.id
# Immediately use for follow-up
response2 = make_request(new_messages, previous_response_id=response_id)
```

### 2. **Handle Expiration Gracefully**
```python
try:
    response = make_request(messages, previous_response_id=cached_id)
except InvalidStatefulMarkerError:
    # Fallback: resend full conversation
    response = make_request(full_conversation_history)
```

### 3. **Model-Specific IDs**
```python
# Store response_id per model
cache = {
    "claude-3.5-sonnet": "resp_abc123",
    "gpt-4o": "resp_xyz789"
}

# Use the correct ID for each model
response_id = cache.get(current_model)
```

### 4. **Clear on Context Changes**
```python
# Clear response_id when:
# - User starts a new conversation
# - Model is switched
# - System prompt changes significantly
# - Authentication changes

def start_new_conversation():
    cache.clear_response_ids()
    cache.clear_messages()
```

### 5. **Monitor Cache Hit Rate**
```python
def track_cache_usage(response):
    cached_tokens = response.usage.input_tokens_details.cached_tokens
    total_tokens = response.usage.input_tokens

    if cached_tokens > 0:
        hit_rate = cached_tokens / total_tokens
        print(f"Cache hit rate: {hit_rate:.1%}")
        metrics.record("cache_hit", hit_rate)
    else:
        metrics.record("cache_miss", 1)
```

## Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Request 1: Initial Request                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ POST /responses                                         │ │
│ │ {                                                       │ │
│ │   "model": "claude-3.5-sonnet",                        │ │
│ │   "input": [system_prompt, user_message]              │ │
│ │ }                                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Response: { id: "resp_abc123", ... }                   │ │
│ │ Cache Created: [system_prompt, user_message]          │ │
│ │ TTL: ~5-60 minutes                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Request 2: Using Cache (within TTL)                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ POST /responses                                         │ │
│ │ {                                                       │ │
│ │   "model": "claude-3.5-sonnet",                        │ │
│ │   "previous_response_id": "resp_abc123",              │ │
│ │   "input": [new_user_message]                         │ │
│ │ }                                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Response: { id: "resp_def456", ... }                   │ │
│ │ Cache Hit: 1234 tokens served from cache              │ │
│ │ New Cache: [previous_context, new_message, response]  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Request 3: After Expiration                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ POST /responses                                         │ │
│ │ {                                                       │ │
│ │   "model": "claude-3.5-sonnet",                        │ │
│ │   "previous_response_id": "resp_abc123",  ← EXPIRED   │ │
│ │   "input": [new_user_message]                         │ │
│ │ }                                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Error: 400 Bad Request                                 │ │
│ │ { "error": { "code": "invalid_stateful_marker" } }    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Retry: POST /responses (without previous_response_id)  │ │
│ │ {                                                       │ │
│ │   "model": "claude-3.5-sonnet",                        │ │
│ │   "input": [full_conversation_history]                │ │
│ │ }                                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Testing Response ID Expiration

### Manual Testing

```python
import time

# 1. Make initial request
response1 = make_request(messages)
response_id = response1.id
print(f"Response ID: {response_id}")

# 2. Wait for expiration (adjust based on provider)
print("Waiting for cache to expire...")
time.sleep(600)  # 10 minutes

# 3. Try to use expired ID
try:
    response2 = make_request(new_messages, previous_response_id=response_id)
    print("Cache still valid!")
except InvalidStatefulMarkerError:
    print("Cache expired as expected")
```

### Automated Testing

Use the validation scripts provided:

```bash
# Run with delays to test expiration
python validate_copilot_simple.py --test-expiration --delay=600
```

## Summary

### Key Takeaways

1. **Response IDs are temporary** - Expect 5-60 minute TTL
2. **Store in conversation history** - Keep with the assistant's message
3. **Handle expiration gracefully** - Implement retry without cache
4. **Model-specific** - Each model has its own response_id
5. **Don't persist long-term** - Clear on new conversations

### When to Clear Response IDs

- ✓ New conversation started
- ✓ Model switched
- ✓ User authentication changed
- ✓ After receiving InvalidStatefulMarker error
- ✓ After long idle periods (>5 minutes)

### When to Keep Response IDs

- ✓ Sequential messages in same conversation
- ✓ Same model being used
- ✓ Within a few minutes of last request
- ✓ Same user session

## References

- [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [GitHub Copilot API Docs](https://docs.github.com/en/copilot/building-copilot-extensions)
