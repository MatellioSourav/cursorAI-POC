# System Architecture

## Architecture Overview

The AI Code Review Bot follows a **modular, service-oriented architecture** with clear separation of concerns.

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  GitHub Actions /                        │
│              Bitbucket Pipelines                         │
│              (CI/CD Platform)                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              AI Code Reviewer                            │
│         (ai_code_reviewer.py)                           │
│  - Orchestrates review process                          │
│  - Manages workflow                                     │
│  - Coordinates services                                 │
└─────┬──────────────┬──────────────┬─────────────────────┘
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  JIRA    │  │   SRS    │  │  OpenAI  │
│ Service  │  │ Service  │  │   API    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │             │
     ▼              ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  JIRA    │  │  SRS     │  │   GPT    │
│   API    │  │  Docs    │  │  Model   │
└──────────┘  └──────────┘  └──────────┘
```

## Service Components

### 1. AI Code Reviewer (Main Orchestrator)

**Responsibilities**:
- Initialize all services
- Coordinate review workflow
- Manage file review process
- Generate review summaries
- Post review comments

**Key Methods**:
- `run()`: Main execution method
- `get_pr_diff()`: Get files changed in PR
- `review_file()`: Review individual file
- `generate_review_summary()`: Create review summary
- `_build_enhanced_prompt()`: Build AI prompt with context

### 2. JIRA Service

**Responsibilities**:
- Extract JIRA keys from text
- Fetch JIRA ticket details
- Normalize JIRA data
- Handle API errors

**Key Methods**:
- `extract_jira_key()`: Extract key using regex
- `find_jira_key()`: Find key in multiple sources
- `fetch_issue()`: Fetch ticket from API
- `_normalize_issue()`: Normalize API response

### 3. SRS Service

**Responsibilities**:
- Discover SRS documents
- Read and combine SRS content
- Format SRS context for prompt
- Handle content limits

**Key Methods**:
- `find_srs_documents()`: Find SRS files
- `read_srs_content()`: Read file content
- `get_srs_context()`: Build formatted context
- `get_srs_summary()`: Get brief summary

## Data Flow

### Review Workflow

```
1. PR Event Triggered
   ↓
2. Bot Initialization
   ├─ Load environment variables
   ├─ Initialize services
   └─ Get PR information
   ↓
3. Load SRS Documents
   ├─ Search configured paths
   ├─ Read SRS files
   └─ Build SRS context
   ↓
4. Fetch JIRA Ticket
   ├─ Extract JIRA key
   ├─ Call JIRA API
   └─ Normalize ticket data
   ↓
5. Get PR Diff
   ├─ Get changed files
   ├─ Filter files
   └─ Prepare file diffs
   ↓
6. Review Each File
   ├─ Build enhanced prompt
   │  ├─ Include SRS context
   │  ├─ Include JIRA context
   │  ├─ Include code changes
   │  └─ Include review requirements
   ├─ Call OpenAI API
   ├─ Parse response
   └─ Post inline comments
   ↓
7. Generate Summary
   ├─ Combine all reviews
   ├─ Add SRS summary
   ├─ Add JIRA compliance
   └─ Generate final verdict
   ↓
8. Post Review
   ├─ Post summary comment
   └─ Submit review verdict
```

## Integration Points

### External Services

1. **GitHub/Bitbucket APIs**
   - PR information
   - Comment posting
   - Review submission

2. **JIRA Internal API**
   - Ticket details
   - Authentication required

3. **OpenAI API**
   - Code analysis
   - GPT model interaction

### Internal Services

1. **JIRA Service** ↔ **JIRA API**
2. **SRS Service** ↔ **File System**
3. **AI Reviewer** ↔ **OpenAI API**
4. **AI Reviewer** ↔ **GitHub/Bitbucket APIs**

## Design Patterns

### 1. Service Pattern
- Each major functionality is a separate service
- Services are loosely coupled
- Easy to test and maintain

### 2. Strategy Pattern
- Different review strategies based on context
- JIRA-aware vs standard review
- SRS-aware vs without SRS

### 3. Template Method Pattern
- Review workflow is templated
- Specific steps can be customized
- Consistent review process

## Error Handling

### Error Handling Strategy

1. **Graceful Degradation**
   - If JIRA unavailable → Skip JIRA-aware review
   - If SRS not found → Continue without SRS
   - If OpenAI fails → Log error, continue

2. **Error Logging**
   - Comprehensive error messages
   - Context information
   - Stack traces for debugging

3. **User Communication**
   - Clear error messages in PR comments
   - Actionable feedback
   - No internal details exposed

## Performance Considerations

### Optimization Strategies

1. **Content Limits**
   - SRS content limited to 10k chars
   - File content limited to 8k chars
   - Prompt size optimization

2. **API Timeouts**
   - 120 seconds for OpenAI
   - 15 seconds for JIRA
   - Prevents hanging

3. **Caching**
   - SRS loaded once per PR
   - JIRA ticket cached during review
   - No redundant API calls

## Security Architecture

### Security Layers

1. **Authentication**
   - API keys from environment variables
   - No hardcoded secrets
   - Secure token storage

2. **Authorization**
   - GitHub/Bitbucket token permissions
   - JIRA token read-only access
   - Principle of least privilege

3. **Data Protection**
   - No sensitive data in logs
   - Secure error handling
   - Input validation

## Scalability

### Current Limitations

- Single PR review at a time
- Sequential file processing
- Limited by OpenAI API rate limits

### Future Enhancements

- Parallel file processing
- Batch API calls
- Caching for repeated reviews

## Monitoring and Observability

### Logging

- Structured logging throughout
- Performance metrics
- Error tracking

### Metrics

- Review completion time
- Files reviewed count
- Issues found count
- API call success/failure rates


