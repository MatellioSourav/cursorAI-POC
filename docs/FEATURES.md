# AI Code Review Bot - Features Documentation

## Overview

The AI Code Review Bot is an intelligent, automated code review system that integrates with GitHub Actions and Bitbucket Pipelines. It provides comprehensive code analysis using OpenAI GPT models, with deep integration to JIRA and SRS documents.

## Core Features

### 1. 🤖 AI-Powered Code Review

**Description**: Automated code review using OpenAI GPT models with comprehensive analysis.

**Capabilities**:
- ✅ Security vulnerability detection
- ✅ Performance issue identification
- ✅ Code quality assessment
- ✅ Best practices validation
- ✅ Bug detection
- ✅ Architecture review

**Review Categories** (22+ SME feedback categories):
1. Authorization (object-level access)
2. External integrations safety
3. DB correctness + constraints
4. Secrets/config discipline
5. Sensitive data/PII exposure
6. Error handling (no internals leak)
7. Code duplication
8. Unused variables/imports
9. Commented-out code
10. Hard-coded values
11. Method/function signatures
12. Semantic logic & business rules
13. Performance (loops, rendering, DB)
14. Promises & async handling
15. Code formatting
16. Security aspects
17. Logging & error handling
18. Code style
19. Documentation
20. Error handling patterns
21. Observability
22. Architecture alignment

**Output Format**:
- ✅ Matches Requirements
- ❌ Missing / Incorrect Implementation
- ⚠️ Suggestions / Improvements
- 📋 Acceptance Criteria Checklist
- 🔚 Final Verdict (Approve / Changes Requested)

### 2. 🎫 JIRA Integration

**Description**: Deep integration with JIRA for context-aware code reviews.

**Features**:
- **Automatic JIRA Key Detection**
  - Extracts from branch names (e.g., `feature/SEC-406-payment`)
  - Extracts from PR titles
  - Extracts from commit messages
  - Uses regex: `[A-Z][A-Z0-9]+-[0-9]+`

- **JIRA Ticket Fetching**
  - Fetches ticket details from internal API
  - Retrieves summary, description, and subtasks
  - Handles errors gracefully

- **Requirement Validation**
  - Validates code against JIRA requirements
  - Checks acceptance criteria coverage
  - Flags missing requirements
  - Detects out-of-scope changes

- **Review Output**
  - JIRA compliance section
  - Acceptance criteria checklist
  - Subtask coverage analysis
  - Final verdict based on JIRA compliance

**Configuration**:
```yaml
env:
  JIRA_API_BASE_URL: ${{ secrets.JIRA_API_BASE_URL }}
  JIRA_PROJECT_ID: ${{ secrets.JIRA_PROJECT_ID }}
  JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
```

**API Endpoint**:
- `GET /api/jira/getissuedetail/{project_id}/{jira_key}`
- Requires Authorization token

### 3. 📋 SRS Integration

**Description**: Integration with Software Requirements Specification documents for project-aware reviews.

**Features**:
- **Automatic SRS Discovery**
  - Searches in `docs/srs/`, `docs/requirements/`, `docs/`
  - Supports `.md`, `.txt`, `.rst` formats
  - Finds common file names (SRS.md, requirements.md, etc.)

- **SRS Context Loading**
  - Reads and combines all SRS documents
  - Formats for AI prompt inclusion
  - Limits content to prevent token overflow (10k chars default)

- **SRS Compliance Checking**
  - Verifies implementation matches SRS specifications
  - Checks functional requirements
  - Validates non-functional requirements
  - Flags architectural violations
  - Validates business rules

**Configuration**:
```yaml
env:
  SRS_PATHS: 'docs/srs/,docs/requirements/,docs/'
  MAX_SRS_LENGTH: '10000'
```

**File Structure**:
```
docs/
└── srs/
    ├── SRS.md
    ├── architecture.md
    └── api-specs.md
```

### 4. 📊 PR-Scoped Review

**Description**: Reviews only files changed in the Pull Request.

**Features**:
- **Strict PR Filtering**
  - Only reviews files in PR diff (`base_sha...head_sha`)
  - Ignores files not part of PR
  - Prevents false positives

- **Smart File Filtering**
  - Skips CI/CD files (`.github/`, `.bitbucket/`)
  - Skips documentation files (unless in src/)
  - Skips generated files (`dist/`, `build/`, `node_modules/`)
  - Skips deleted files
  - Skips demo/example files

- **Commit-Based Context**
  - Identifies commits with JIRA key (for context)
  - Doesn't filter files based on commits (only PR diff)

### 5. 💬 Comprehensive Review Output

**Description**: Structured, actionable review feedback.

**Features**:
- **Inline Comments**
  - Line-specific feedback for critical issues
  - Severity levels (error, warning, info)
  - Actionable suggestions

- **Review Summary**
  - Overview of all issues
  - JIRA compliance status
  - SRS compliance status
  - Acceptance criteria checklist
  - Subtask coverage
  - Final verdict

- **Structured Format**
  - Markdown formatting
  - Emoji indicators for quick scanning
  - Organized by category
  - Clear action items

### 6. 🔒 Security & Safety

**Description**: Secure and safe code review process.

**Features**:
- **No Hardcoded Secrets**
  - All credentials via environment variables
  - Secure token handling
  - No sensitive data in code

- **Error Handling**
  - Graceful degradation
  - No internal details exposure
  - Clear error messages
  - Comprehensive logging

- **API Security**
  - Timeout protection (120s for OpenAI, 15s for JIRA)
  - Retry logic for transient failures
  - Secure API communication

### 7. ⚙️ Configuration & Flexibility

**Description**: Highly configurable and flexible setup.

**Features**:
- **Environment Variables**
  - All settings via environment variables
  - No hardcoded values
  - Easy configuration

- **Optional Features**
  - JIRA integration (optional)
  - SRS integration (optional)
  - Works without either

- **Multiple Platforms**
  - GitHub Actions support
  - Bitbucket Pipelines support
  - Easy to extend to other platforms

## Feature Comparison

| Feature | Without JIRA | With JIRA | With JIRA + SRS |
|---------|-------------|-----------|-----------------|
| Code Quality Review | ✅ | ✅ | ✅ |
| Security Checks | ✅ | ✅ | ✅ |
| Performance Analysis | ✅ | ✅ | ✅ |
| JIRA Requirement Validation | ❌ | ✅ | ✅ |
| Acceptance Criteria Check | ❌ | ✅ | ✅ |
| SRS Compliance | ❌ | ❌ | ✅ |
| Architecture Validation | ❌ | ❌ | ✅ |
| Business Rule Validation | ❌ | ❌ | ✅ |

## Usage Examples

### Example 1: Basic Review (No JIRA/SRS)

```yaml
# .github/workflows/ai-code-review.yml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Result**: Standard code review with quality, security, and performance checks.

### Example 2: JIRA-Aware Review

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  JIRA_API_BASE_URL: ${{ secrets.JIRA_API_BASE_URL }}
  JIRA_PROJECT_ID: ${{ secrets.JIRA_PROJECT_ID }}
  JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
```

**Result**: Code review validated against JIRA ticket requirements.

### Example 3: Full Integration (JIRA + SRS)

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  JIRA_API_BASE_URL: ${{ secrets.JIRA_API_BASE_URL }}
  JIRA_PROJECT_ID: ${{ secrets.JIRA_PROJECT_ID }}
  JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
  SRS_PATHS: 'docs/srs/,docs/requirements/'
  MAX_SRS_LENGTH: '15000'
```

**Result**: Complete project-aware review with JIRA and SRS validation.

## Performance

### Review Time
- **Small PR (1-2 files)**: 1-2 minutes
- **Medium PR (3-5 files)**: 2-4 minutes
- **Large PR (6-10 files)**: 4-8 minutes

### Token Usage
- **Per file**: ~3000-5000 tokens (without SRS)
- **With SRS**: ~5500-7500 tokens per file
- **Cost**: ~$0.10-0.20 per PR

### Optimization
- Content limits prevent excessive token usage
- SRS loaded once per PR (not per file)
- Timeout protection prevents hanging
- Efficient prompt building

## Limitations

1. **OpenAI API Rate Limits**: Subject to OpenAI API rate limits
2. **Token Limits**: Large files may be truncated
3. **Single PR**: Reviews one PR at a time
4. **Sequential Processing**: Files reviewed sequentially (can be parallelized)

## Future Enhancements

- [ ] Parallel file processing
- [ ] S3-based SRS storage
- [ ] Custom review rules
- [ ] Review caching
- [ ] Multi-language support
- [ ] Custom AI models
- [ ] Review templates
- [ ] Integration with more platforms

## Support

For feature requests or issues:
1. Check documentation in `docs/` folder
2. Review GitHub Actions/Bitbucket Pipeline logs
3. Verify configuration settings
4. Check environment variables

