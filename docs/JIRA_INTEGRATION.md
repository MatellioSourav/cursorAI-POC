# JIRA Integration Guide

## Overview

The AI Code Review Bot integrates with JIRA to provide context-aware code reviews. It automatically detects JIRA tickets, fetches requirements, and validates code against them.

## Features

### 1. Automatic JIRA Key Detection

The bot automatically extracts JIRA ticket keys from:

- **Branch Names**: `feature/SEC-406-payment-gateway` → `SEC-406`
- **PR Titles**: `SEC-406: Implement payment gateway` → `SEC-406`
- **Commit Messages**: `Fix SEC-406 bug` → `SEC-406`

**Regex Pattern**: `[A-Z][A-Z0-9]+-[0-9]+`

### 2. JIRA Ticket Fetching

Fetches ticket details from internal JIRA API:
- Summary
- Description
- Subtasks
- Acceptance criteria

### 3. Requirement Validation

Validates code against:
- JIRA ticket description
- Acceptance criteria
- Subtask requirements
- Scope alignment

## Setup

### Step 1: Configure JIRA API

Add these secrets to your repository:

1. **JIRA_API_BASE_URL**: Base URL for JIRA API
   - Example: `http://hrm.matellio.com/api/jira`

2. **JIRA_PROJECT_ID**: Your JIRA project ID
   - Example: `1554`

3. **JIRA_API_TOKEN**: Authentication token
   - Get from JIRA admin
   - Must have read access to tickets

### Step 2: Update Workflow

#### GitHub Actions

Add to `.github/workflows/ai-code-review.yml`:

```yaml
env:
  JIRA_API_BASE_URL: ${{ secrets.JIRA_API_BASE_URL }}
  JIRA_PROJECT_ID: ${{ secrets.JIRA_PROJECT_ID }}
  JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
```

#### Bitbucket Pipelines

Add to `bitbucket-pipelines.yml`:

```yaml
variables:
  JIRA_API_BASE_URL: $JIRA_API_BASE_URL
  JIRA_PROJECT_ID: $JIRA_PROJECT_ID
  JIRA_API_TOKEN: $JIRA_API_TOKEN
```

### Step 3: Create JIRA Tickets

When creating PRs, ensure:
- Branch name contains JIRA key: `feature/SEC-406-...`
- PR title contains JIRA key: `SEC-406: ...`
- Commit messages reference JIRA key

## API Integration

### Endpoint

```
GET /api/jira/getissuedetail/{project_id}/{jira_key}
```

### Request Headers

```
Authorization: {JIRA_API_TOKEN}
```

### Response Format

```json
{
  "status": "success",
  "data": {
    "id": "37113",
    "key": "SEC-406",
    "summary": "Implement Payment Gateway Integration",
    "description": "...",
    "subtasks": [
      {
        "id": "37119",
        "key": "SEC-406-1",
        "summary": "Design payment gateway API endpoints"
      }
    ]
  }
}
```

## How It Works

### Workflow

```
1. PR Created/Updated
   ↓
2. Extract JIRA Key
   ├─ From branch name
   ├─ From PR title
   └─ From commit messages
   ↓
3. Fetch JIRA Ticket
   ├─ Call internal API
   ├─ Get ticket details
   └─ Normalize data
   ↓
4. Build Review Context
   ├─ Include JIRA summary
   ├─ Include description
   ├─ Include subtasks
   └─ Include acceptance criteria
   ↓
5. Review Code
   ├─ Validate against requirements
   ├─ Check acceptance criteria
   ├─ Flag missing requirements
   └─ Detect scope violations
   ↓
6. Generate Review
   ├─ JIRA compliance section
   ├─ Acceptance criteria checklist
   ├─ Subtask coverage
   └─ Final verdict
```

### Review Output

The bot includes:

1. **JIRA Ticket Information**
   - Ticket key and summary
   - Description
   - Subtasks (if any)

2. **JIRA Compliance Check**
   - ✅ Matches JIRA Requirements
   - ❌ Missing / Incorrect Implementation
   - ⚠️ Suggestions / Improvements

3. **Acceptance Criteria Checklist**
   - Lists all acceptance criteria
   - Marks which are met/missing
   - Provides line references

4. **Subtask Coverage**
   - Lists all subtasks
   - Checks implementation coverage
   - Flags missing subtasks

5. **Final Verdict**
   - Approve (if all requirements met)
   - Changes Requested (if requirements missing)

## Error Handling

### No JIRA Key Found

**Behavior**: Bot posts comment requesting JIRA key and skips review.

**Comment**:
```
⚠️ JIRA ticket required for code review.

Please add a JIRA ticket key to:
- Branch name (e.g., feature/SEC-406-...)
- PR title (e.g., SEC-406: ...)
- Commit messages

Then update this PR to trigger review.
```

### JIRA API Error

**Behavior**: Bot logs error and skips JIRA-aware review.

**Common Errors**:
- `404 - Token is required`: Token not set or invalid
- `404 - Jira issue not found`: Ticket doesn't exist
- `Timeout`: API took too long to respond

**Solution**: Check token and API configuration.

### Ticket Not Found

**Behavior**: Bot comments on PR and skips review.

**Comment**:
```
⚠️ Could not fetch JIRA issue SEC-406.

Please verify:
1. Ticket SEC-406 exists in JIRA
2. JIRA_API_TOKEN has read access
3. JIRA_PROJECT_ID is correct
```

## Best Practices

### 1. Consistent Naming

- Use JIRA key in branch names: `feature/SEC-406-payment`
- Include JIRA key in PR titles: `SEC-406: Implement payment gateway`
- Reference JIRA in commit messages

### 2. Clear Requirements

- Write detailed JIRA descriptions
- List all acceptance criteria
- Include subtasks for complex features
- Specify security and performance requirements

### 3. Scope Alignment

- Keep PRs focused on single JIRA ticket
- Avoid mixing multiple tickets in one PR
- Ensure all changed files relate to ticket

### 4. Regular Updates

- Update JIRA ticket as requirements change
- Keep acceptance criteria current
- Close completed subtasks

## Troubleshooting

### Issue: JIRA key not detected

**Check**:
1. Branch name format: `feature/SEC-406-...`
2. PR title contains JIRA key
3. Commit messages reference JIRA key

**Solution**: Update branch name or PR title.

### Issue: Token error

**Check**:
1. `JIRA_API_TOKEN` is set in secrets
2. Token is valid and not expired
3. Token has read permissions

**Solution**: Regenerate token and update secret.

### Issue: Ticket not found

**Check**:
1. Ticket exists in JIRA
2. `JIRA_PROJECT_ID` is correct
3. Token has access to project

**Solution**: Verify ticket exists and project ID.

## Examples

### Example 1: Simple Ticket

**JIRA Ticket**: SEC-406
**Summary**: Implement Payment Gateway Integration
**Description**: Add payment processing functionality

**Review Output**:
- ✅ Validates payment endpoints exist
- ✅ Checks authentication requirements
- ✅ Verifies error handling
- ✅ Flags missing requirements

### Example 2: Ticket with Subtasks

**JIRA Ticket**: SEC-406
**Subtasks**:
- SEC-406-1: Design API endpoints
- SEC-406-2: Implement payment service
- SEC-406-3: Add unit tests

**Review Output**:
- ✅ Checks each subtask implementation
- ✅ Flags missing subtasks
- ✅ Provides subtask coverage report

## API Reference

### JiraService Class

**Location**: `.github/scripts/jira_service.py`

**Methods**:
- `extract_jira_key(text)`: Extract key from text
- `find_jira_key()`: Find key in branch/PR/commits
- `fetch_issue(issue_key)`: Fetch ticket from API
- `_normalize_issue(data, key)`: Normalize API response

## Summary

JIRA integration enables:
- ✅ Context-aware code reviews
- ✅ Requirement validation
- ✅ Acceptance criteria checking
- ✅ Scope alignment verification
- ✅ Comprehensive review output

Simply configure the API credentials and the bot will automatically use JIRA tickets for reviews!

