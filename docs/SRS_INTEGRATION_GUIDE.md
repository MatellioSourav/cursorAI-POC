# SRS Integration Guide

## Overview

The AI Code Review Bot now supports **Software Requirements Specification (SRS)** documents integration. This allows the bot to have complete knowledge of your project requirements and review code against SRS specifications.

## What is SRS Integration?

SRS integration enables the AI code review bot to:
- ✅ Understand project architecture and design patterns
- ✅ Review code against functional and non-functional requirements
- ✅ Validate business rules and domain logic
- ✅ Detect architectural violations
- ✅ Ensure consistency with project specifications

## How It Works

1. **SRS Document Discovery**: Bot automatically searches for SRS documents in configured paths
2. **Content Loading**: Reads and combines all SRS documents
3. **Context Integration**: Includes SRS context in AI review prompt
4. **Compliance Checking**: AI reviews code against SRS requirements

## Setup

### Step 1: Create SRS Directory Structure

Create the following directory structure in your repository:

```
your-repo/
└── docs/
    └── srs/
        ├── SRS.md
        ├── architecture.md
        ├── api-specs.md
        └── database-schema.md
```

### Step 2: Add SRS Documents

Place your SRS documents in the `docs/srs/` folder. Supported formats:
- **Markdown** (`.md`) - Recommended
- **Plain Text** (`.txt`)
- **reStructuredText** (`.rst`)

### Step 3: Document Structure

Your SRS documents should include:
- **Functional Requirements**: What the system should do
- **Non-Functional Requirements**: Performance, security, scalability
- **Architecture**: System design, patterns, components
- **API Specifications**: Endpoints, request/response formats
- **Database Schema**: Tables, relationships, constraints
- **Business Rules**: Domain logic, validation rules

## Configuration

### Default Configuration

By default, the bot searches for SRS documents in:
- `docs/srs/` (primary location)
- `docs/requirements/` (alternative)
- `docs/` (fallback)

### Custom Configuration

You can configure custom paths via environment variables:

#### GitHub Actions

Add to `.github/workflows/ai-code-review.yml`:

```yaml
env:
  SRS_PATHS: 'docs/srs/,specs/,project-docs/'
  MAX_SRS_LENGTH: '15000'
```

#### Bitbucket Pipelines

Add to `bitbucket-pipelines.yml`:

```yaml
variables:
  SRS_PATHS: 'docs/srs/,specs/,project-docs/'
  MAX_SRS_LENGTH: '15000'
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SRS_PATHS` | `docs/srs/,docs/requirements/,docs/` | Comma-separated paths to search for SRS documents |
| `MAX_SRS_LENGTH` | `10000` | Maximum characters to include from SRS documents (to avoid token limits) |

## Example SRS Documents

### Example 1: Main SRS Document (`docs/srs/SRS.md`)

```markdown
# Software Requirements Specification

## Project Overview
This document describes the requirements for the Payment Gateway Integration System.

## Functional Requirements

### FR-1: Payment Processing
- System shall process credit card payments
- System shall support multiple payment gateways (Stripe, PayPal)
- System shall handle payment failures gracefully

### FR-2: Transaction Management
- System shall store all transaction records
- System shall provide transaction history
- System shall support refund processing

## Non-Functional Requirements

### NFR-1: Performance
- Payment processing must complete within 5 seconds
- System must handle 1000 concurrent transactions

### NFR-2: Security
- All payment data must be encrypted
- PCI DSS compliance required
- No sensitive data in logs

## Architecture
- Microservices architecture
- RESTful API design
- Event-driven communication
```

### Example 2: Architecture Document (`docs/srs/architecture.md`)

```markdown
# System Architecture

## Architecture Pattern
- **Pattern**: Microservices
- **Communication**: REST APIs and Message Queue

## Components
1. **Payment Service**: Handles payment processing
2. **Transaction Service**: Manages transaction records
3. **Notification Service**: Sends payment notifications

## Database Design
- **Transactions Table**: Stores payment transactions
- **Users Table**: Stores user information
- **Indexes**: Required on transaction_id, user_id, created_at
```

### Example 3: API Specifications (`docs/srs/api-specs.md`)

```markdown
# API Specifications

## Payment Endpoints

### POST /api/payments/process
- **Description**: Process a payment
- **Authentication**: Required (JWT)
- **Request Body**:
  ```json
  {
    "amount": 100.00,
    "currency": "USD",
    "paymentMethod": "credit_card"
  }
  ```
- **Response**: Transaction ID and status

### GET /api/payments/:transactionId
- **Description**: Get payment details
- **Authentication**: Required
- **Authorization**: User can only access their own transactions
```

## How Reviews Work with SRS

When SRS documents are present, the AI reviewer will:

1. **Load SRS Context**: Reads all SRS documents at startup
2. **Include in Prompt**: Adds SRS content to AI review prompt
3. **Compliance Checking**: Reviews code against SRS requirements
4. **Flag Deviations**: Identifies code that doesn't match SRS
5. **Architecture Validation**: Checks architectural alignment

### Review Output

The review will include:

```
## 📚 SRS Context

Found 3 SRS document(s): docs/srs/SRS.md, docs/srs/architecture.md, docs/srs/api-specs.md

## Review Comments

❌ Missing Implementation: SRS requires payment retry logic, but code doesn't implement it
⚠️  Architecture Violation: SRS specifies microservices, but code uses monolithic structure
✅ Requirement Met: Payment processing endpoint matches SRS specification
```

## Best Practices

### 1. Keep SRS Documents Updated
- Update SRS when requirements change
- Version control SRS documents
- Keep them synchronized with code

### 2. Organize by Topic
- Separate documents by concern (architecture, API, database)
- Use clear, descriptive file names
- Include table of contents for large documents

### 3. Be Specific
- Include concrete requirements, not vague descriptions
- Specify performance metrics
- Define security requirements clearly

### 4. Include Examples
- Provide code examples where relevant
- Include API request/response examples
- Show database schema diagrams

### 5. Document Business Rules
- Clearly state business logic
- Include validation rules
- Document edge cases

## Troubleshooting

### SRS Documents Not Found

**Problem**: Bot reports "No SRS documents found"

**Solutions**:
1. Check that `docs/srs/` folder exists
2. Verify files have supported extensions (`.md`, `.txt`, `.rst`)
3. Check file permissions (must be readable)
4. Verify `SRS_PATHS` environment variable if using custom paths

### SRS Content Too Large

**Problem**: SRS documents exceed token limits

**Solutions**:
1. Increase `MAX_SRS_LENGTH` environment variable
2. Split large documents into smaller files
3. Remove unnecessary content
4. Summarize detailed sections

### SRS Not Included in Review

**Problem**: Review doesn't mention SRS compliance

**Solutions**:
1. Verify SRS documents are in correct location
2. Check bot logs for SRS loading messages
3. Ensure files are committed to repository
4. Verify file extensions are supported

## Performance Impact

Including SRS documents:
- **Time**: Adds ~5-10 seconds per file review
- **Tokens**: Adds ~2500 tokens per 10k chars of SRS
- **Cost**: Minimal increase (~$0.01-0.02 per PR)

**Recommendation**: Keep SRS documents concise and focused on essential requirements.

## Examples

### Example Project Structure

```
project/
├── docs/
│   └── srs/
│       ├── SRS.md                    # Main requirements
│       ├── architecture.md           # System design
│       ├── api-specs.md              # API documentation
│       ├── database-schema.md        # Database design
│       └── security-requirements.md  # Security specs
├── .github/
│   └── scripts/
│       ├── ai_code_reviewer.py
│       ├── jira_service.py
│       └── srs_service.py
└── src/
    └── ...
```

## FAQ

### Q: Do I need SRS documents for the bot to work?
**A**: No, SRS integration is optional. The bot works without SRS documents.

### Q: Can I use multiple SRS documents?
**A**: Yes, the bot will combine all SRS documents found in configured paths.

### Q: What if my SRS is in a different location?
**A**: Configure custom paths using the `SRS_PATHS` environment variable.

### Q: How much SRS content can I include?
**A**: Default is 10,000 characters. You can increase this via `MAX_SRS_LENGTH`.

### Q: Will SRS slow down reviews?
**A**: Slightly (~5-10 seconds per file), but provides much better review quality.

## Support

For issues or questions:
1. Check bot logs for SRS loading messages
2. Verify SRS document format and location
3. Review configuration settings
4. Check GitHub Actions/Bitbucket Pipeline logs

## Summary

SRS integration enables the AI code review bot to:
- ✅ Have complete project knowledge
- ✅ Review against project requirements
- ✅ Detect architectural violations
- ✅ Validate business logic
- ✅ Ensure consistency with specifications

Simply add your SRS documents to `docs/srs/` and the bot will automatically use them!


