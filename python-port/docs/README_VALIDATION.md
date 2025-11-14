# GitHub Copilot Responses API Validation Scripts

These scripts validate whether GitHub Copilot models (including Claude Sonnet) support the Responses API with prompt caching.

## Scripts

### 1. `validate_copilot_simple.py` (Recommended)
Simple script using only the `requests` library. Tests both Chat Completions and Responses APIs.

**Requirements:**
```bash
pip install requests
```

**Usage:**
```bash
# Set your GitHub token
export GITHUB_TOKEN="your_github_token_here"

# Run the script
python validate_copilot_simple.py
```

### 2. `validate_copilot_responses_api.py`
More comprehensive script using LiteLLM for additional model testing capabilities.

**Requirements:**
```bash
pip install litellm requests
```

**Usage:**
```bash
export GITHUB_TOKEN="your_github_token_here"
python validate_copilot_responses_api.py
```

### 3. `test_response_id_expiration.py` (NEW)
Tests how long `response_id` values remain valid before expiring.

**Requirements:**
```bash
pip install requests
```

**Usage:**
```bash
export GITHUB_TOKEN="your_github_token_here"

# Test with 5 minute delay (default)
python test_response_id_expiration.py --delay 300

# Test with 10 minute delay
python test_response_id_expiration.py --delay 600

# Test specific model
python test_response_id_expiration.py --model claude-3.5-sonnet --delay 300

# Quick test (30 seconds)
python test_response_id_expiration.py --delay 30
```

**What it does:**
1. Makes an initial request and captures the `response_id`
2. Waits for the specified delay
3. Attempts to use the `response_id` in a follow-up request
4. Reports whether the ID is still valid or has expired

## Getting a GitHub Token

You need a GitHub token with Copilot access:

1. Go to https://github.com/settings/tokens
2. Generate a new token (classic) with `copilot` scope
3. Or use your existing GitHub Copilot authentication token

Alternatively, you can extract your token from VSCode:
- Open VSCode Developer Tools (Help → Toggle Developer Tools)
- Go to Application → Local Storage
- Look for GitHub authentication tokens

## What the Scripts Test

### 1. Model Discovery
- Lists all available GitHub Copilot models
- Shows which models support the Responses API
- Identifies models with caching capabilities

### 2. Chat Completions API
- Tests the traditional `/chat/completions` endpoint
- Shows token usage
- Validates basic model functionality

### 3. Responses API with Caching
- Tests the newer `/responses` endpoint
- Makes two sequential requests:
  1. **First request**: Sends a long system prompt
  2. **Second request**: Uses `previous_response_id` to reference cached context
- Measures cached tokens to validate caching is working

## Expected Output

### For Models WITH Caching Support (e.g., Claude Sonnet)

```
✓✓ PROMPT CACHING IS WORKING!
   1234 tokens were served from cache
   Time saved: 0.5s (45.2%)
```

### For Models WITHOUT Caching Support

```
⚠ No cached tokens detected
  This could mean:
  - Model doesn't support caching
  - Cache hasn't been populated yet
  - previous_response_id not working as expected
```

## Understanding the Results

### Responses API Support
If a model lists `/responses` in its `supported_endpoints`, it supports the Responses API.

### Prompt Caching
Caching is indicated by:
- `cached_tokens > 0` in the usage statistics
- Faster response times on subsequent requests
- The `previous_response_id` parameter working correctly

### Models to Test

Common GitHub Copilot models:
- `gpt-4o` - OpenAI GPT-4 Optimized
- `gpt-4o-mini` - Smaller, faster GPT-4
- `claude-3.5-sonnet` - Anthropic Claude 3.5 Sonnet
- `claude-3.7-sonnet` - Anthropic Claude 3.7 Sonnet (if available)
- `o1` - OpenAI O1 reasoning model
- `o1-mini` - Smaller O1 model

## Troubleshooting

### Authentication Errors
```
Error: GitHub API key not found
```
**Solution:** Set the `GITHUB_TOKEN` environment variable

### 401 Unauthorized
```
✗ Failed to fetch models: HTTP 401
```
**Solution:** Your token may not have Copilot access or has expired

### 404 Not Found
```
✗ Request failed: HTTP 404
```
**Solution:** The model may not be available in your region or subscription

### No Cached Tokens
```
⚠ No cached tokens detected
```
**Possible reasons:**
1. Model doesn't support the Responses API
2. Model doesn't support prompt caching
3. The cache hasn't been populated (try running again)
4. The `previous_response_id` mechanism isn't working

## How Prompt Caching Works

### Traditional Chat Completions API
```
Request 1: [System Prompt] + [User Message 1] → Response 1
Request 2: [System Prompt] + [User Message 1] + [Response 1] + [User Message 2] → Response 2
```
Every request reprocesses the entire conversation history.

### Responses API with Caching
```
Request 1: [System Prompt] + [User Message 1] → Response 1 (ID: abc123)
Request 2: previous_response_id=abc123 + [User Message 2] → Response 2
```
The second request references the cached context, only processing new messages.

### Benefits
- **Reduced latency**: Cached tokens are served instantly
- **Lower costs**: Cached tokens are typically cheaper
- **Better performance**: Less processing required

## VSCode Integration

VSCode uses the Responses API when:
1. `github.copilot.chat.useResponsesApi` is enabled (default: `true`)
2. The model's metadata includes `/responses` in `supported_endpoints`
3. The model is configured to support the Responses API by GitHub

You can check your VSCode settings:
```json
{
  "github.copilot.chat.useResponsesApi": true
}
```

## API Documentation

- [GitHub Copilot API](https://docs.github.com/en/copilot/building-copilot-extensions)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [Anthropic Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

## License

These scripts are provided as-is for testing and validation purposes.
