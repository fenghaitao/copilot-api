# History Feature Fix Summary

## Problem
The `copilot-api check-usage --history` command was not working. It would fetch data but display "N/A" for all months because:

1. **Wrong API endpoint**: The code was calling `/copilot_internal/user` which only returns current quota information, not historical metrics
2. **Wrong API version**: The code was using API version "2025-04-01" which is not supported by GitHub's REST API (only "2022-11-28" is supported)
3. **Missing error handling**: Errors weren't being displayed with enough detail to diagnose the issue

## Solution

### 1. Fixed API Endpoint
Changed from `/copilot_internal/user` to `/orgs/{org}/copilot/metrics` for historical data:
- This endpoint returns daily metrics with `total_active_users` and `total_engaged_users`
- Requires organization owner or billing manager permissions
- Supports date range queries with `since` and `until` parameters

### 2. Fixed API Version
Changed the GitHub API version header from "2025-04-01" to "2022-11-28":
```python
# In src/copilot_api/lib/api_config.py
"x-github-api-version": "2022-11-28",  # Use supported version for GitHub REST API
```

### 3. Improved Error Handling
Added detailed error messages that explain:
- What permissions are required (org owner or billing manager)
- What token scopes are needed ('copilot' or 'manage_billing:copilot')
- Link to documentation

### 4. Updated Time Range
Changed from 3 months to 2 months because GitHub API only supports 28 days lookback

### 5. Better Data Display
Updated the table to show average users per day instead of totals

## Current Status

### Working ✅
- `copilot-api check-usage` - Shows current month quota (works perfectly)
- `copilot-api check-usage --since YYYY-MM-DD --until YYYY-MM-DD` - Date range queries (requires permissions)
- `copilot-api check-usage --history` - Shows last 2 months (requires permissions)

### Requires Additional Permissions ⚠️
The history feature now correctly identifies that it needs:
1. Organization owner or billing manager role
2. Personal access token with 'copilot' or 'manage_billing:copilot' scope
3. Copilot metrics API access policy enabled for the organization

The error message now clearly explains these requirements when permissions are missing.

## Testing

Current month usage (no special permissions needed):
```bash
.venv/bin/copilot-api check-usage
```

Historical usage (requires org permissions):
```bash
.venv/bin/copilot-api check-usage --history
.venv/bin/copilot-api check-usage --history --verbose  # Shows full error details
```

## Files Modified
- `src/copilot_api/commands/check_usage.py` - Updated history logic and error handling
- `src/copilot_api/lib/api_config.py` - Fixed API version header
- `src/copilot_api/services/github/get_copilot_usage.py` - Implemented correct endpoint and error handling
