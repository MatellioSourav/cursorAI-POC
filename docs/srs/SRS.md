# Software Requirements Specification (SRS)

## Project Overview

This document describes the requirements for the AI-Powered Code Review Bot with JIRA and SRS integration.

## Functional Requirements

### FR-1: Automated Code Review
- System shall automatically review Pull Requests using AI
- System shall provide detailed code analysis
- System shall flag security vulnerabilities
- System shall identify performance issues
- System shall check code quality standards

### FR-2: JIRA Integration
- System shall extract JIRA ticket keys from branch names, PR titles, and commit messages
- System shall fetch JIRA ticket details from internal API
- System shall validate code against JIRA requirements
- System shall check acceptance criteria coverage
- System shall flag missing requirements

### FR-3: SRS Integration
- System shall read SRS documents from configured paths
- System shall include SRS context in code reviews
- System shall validate code against SRS specifications
- System shall check architectural alignment
- System shall verify business rule compliance

### FR-4: Review Output
- System shall post inline comments for critical issues
- System shall generate comprehensive review summary
- System shall provide structured feedback (matches, missing, suggestions)
- System shall include acceptance criteria checklist
- System shall provide final verdict (Approve/Changes Requested)

## Non-Functional Requirements

### NFR-1: Performance
- Code review should complete within 2-5 minutes for typical PRs
- API calls should have timeout protection (120 seconds)
- Should handle PRs with up to 20 files efficiently

### NFR-2: Security
- No hardcoded secrets or API keys
- Secure handling of authentication tokens
- No sensitive data in logs
- Proper error handling without internal details exposure

### NFR-3: Reliability
- Graceful handling of API failures
- Retry logic for transient failures
- Fallback behavior when services unavailable
- Comprehensive error logging

### NFR-4: Maintainability
- Modular code structure
- Clear separation of concerns
- Comprehensive documentation
- Easy configuration via environment variables

## Architecture

### System Components

1. **AI Code Reviewer** (`ai_code_reviewer.py`)
   - Main orchestrator
   - Coordinates review process
   - Manages file review workflow

2. **JIRA Service** (`jira_service.py`)
   - JIRA key extraction
   - JIRA API integration
   - Ticket data normalization

3. **SRS Service** (`srs_service.py`)
   - SRS document discovery
   - Content loading and formatting
   - Context preparation

4. **OpenAI Integration**
   - GPT model for code analysis
   - Structured prompt building
   - Response parsing

5. **GitHub/Bitbucket Integration**
   - PR information fetching
   - Review comment posting
   - Review submission

### Data Flow

```
PR Event → Bot Initialization → Load SRS → Fetch JIRA → Get PR Diff → 
Review Files → Generate Summary → Post Review
```

## API Specifications

### Internal APIs

#### JIRA API
- **Endpoint**: `GET /api/jira/getissuedetail/{project_id}/{jira_key}`
- **Authentication**: Authorization header with token
- **Response**: JIRA ticket details (summary, description, subtasks)

### External APIs

#### OpenAI API
- **Endpoint**: `POST https://api.openai.com/v1/chat/completions`
- **Authentication**: API key in header
- **Purpose**: Code review analysis

#### GitHub API
- **Endpoints**: PR info, comment posting, review submission
- **Authentication**: GitHub token
- **Purpose**: PR interaction

## Database Requirements

Not applicable - Bot is stateless and doesn't use a database.

## Security Requirements

1. **Authentication**
   - All API keys stored as secrets
   - No hardcoded credentials
   - Secure token handling

2. **Authorization**
   - GitHub/Bitbucket token with appropriate permissions
   - JIRA token with read-only access

3. **Data Protection**
   - No sensitive data in logs
   - Secure error handling
   - No internal details exposure

## Testing Requirements

1. **Unit Tests**
   - Test JIRA key extraction
   - Test SRS document loading
   - Test prompt building

2. **Integration Tests**
   - Test JIRA API integration
   - Test OpenAI API calls
   - Test GitHub API interactions

3. **End-to-End Tests**
   - Test complete review workflow
   - Test error scenarios
   - Test with real PRs

## Configuration

### Required Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `GITHUB_TOKEN` / `BITBUCKET_TOKEN`: Repository access token
- `JIRA_API_BASE_URL`: JIRA API base URL
- `JIRA_PROJECT_ID`: JIRA project ID
- `JIRA_API_TOKEN`: JIRA API authentication token

### Optional Environment Variables

- `SRS_PATHS`: Comma-separated SRS document paths
- `MAX_SRS_LENGTH`: Maximum SRS content length

## Business Rules

1. **JIRA Ticket Required**: Bot requires JIRA ticket for review (can be configured)
2. **PR-Scoped Review**: Only files in PR diff are reviewed
3. **File Filtering**: CI/CD files, docs, generated files are skipped
4. **Review Structure**: Must follow specified output format
5. **Final Verdict**: Based on critical issues and missing requirements

## Acceptance Criteria

1. ✅ Bot successfully extracts JIRA keys from various sources
2. ✅ Bot fetches JIRA ticket details correctly
3. ✅ Bot loads SRS documents from configured paths
4. ✅ Bot reviews code against JIRA and SRS requirements
5. ✅ Bot posts structured review comments
6. ✅ Bot generates comprehensive review summary
7. ✅ Bot handles errors gracefully
8. ✅ Bot respects PR scope (only reviews changed files)


