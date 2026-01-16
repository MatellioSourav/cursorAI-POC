# 🎫 Bitbucket JIRA Integration - Complete

## ✅ Status: **FULLY UPDATED**

The Bitbucket version of the AI Code Review bot has been **fully updated** with the same JIRA integration features as the GitHub version.

---

## 📦 **What Was Updated**

### **1. New File Added**
- **`.bitbucket/scripts/jira_service.py`** - JIRA API integration module (copied from GitHub version)

### **2. Enhanced Files**
- **`.bitbucket/scripts/ai_code_reviewer_bitbucket.py`** - Added JIRA integration:
  - JIRA ticket detection from branch name, PR title, commit messages
  - JIRA API integration to fetch ticket details
  - JIRA-aware AI prompts
  - Acceptance criteria validation
  - Out-of-scope file detection
  - Enhanced summary with JIRA compliance section
  - PR link posting to JIRA ticket

- **`bitbucket-pipelines.yml`** - Added JIRA environment variables:
  - `JIRA_BASE_URL`
  - `JIRA_EMAIL`
  - `JIRA_API_TOKEN`

---

## 🔧 **Configuration for Bitbucket**

### **Step 1: Add JIRA Variables to Bitbucket**

1. Go to your Bitbucket repository
2. Navigate to: **Repository Settings** → **Pipelines** → **Repository variables**
3. Add these variables:

```
JIRA_BASE_URL = https://your-company.atlassian.net
JIRA_EMAIL = your-email@company.com
JIRA_API_TOKEN = your-jira-api-token
```

**Note:** These are optional. If not set, the bot works in standard (non-JIRA) mode.

### **Step 2: Get JIRA API Token**

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Copy the token
4. Add to Bitbucket Repository variables as `JIRA_API_TOKEN`

---

## 🎯 **Features (Same as GitHub Version)**

### ✅ **JIRA Ticket Detection**
- Extracts JIRA key from branch name, PR title, commit messages
- Regex pattern: `[A-Z][A-Z0-9]+-[0-9]+`
- If no ticket found: Posts comment asking for JIRA ticket, skips review

### ✅ **JIRA API Integration**
- Fetches issue details using JIRA REST API v3
- Extracts: Summary, Description, Acceptance Criteria, Issue Type, Priority

### ✅ **Context-Aware AI Review**
- Verifies implementation matches JIRA requirements
- Flags missing acceptance criteria
- Detects out-of-scope file changes
- Compares code against JIRA description

### ✅ **Enhanced Review Output**
- ✅ Matches requirements
- ❌ Missing / Incorrect
- ⚠️ Suggestions
- 📋 Acceptance Criteria Checklist

### ✅ **PR Linking**
- Automatically adds PR link as comment on JIRA ticket

---

## 📊 **How It Works**

### **Detection Flow (Bitbucket)**

```
1. PR Created in Bitbucket
   ↓
2. Pipeline triggers
   ↓
3. Extract JIRA key from:
   - Branch name (BITBUCKET_BRANCH)
   - PR title (fetched from Bitbucket API)
   - Commit messages
   ↓
4. If JIRA key found:
   - Fetch ticket from JIRA API
   - Enhance AI prompt with JIRA context
   - Review code against requirements
   ↓
5. If no JIRA key:
   - Post comment asking for JIRA ticket
   - Skip AI review
```

---

## 🔍 **Key Differences from GitHub Version**

| Aspect | GitHub | Bitbucket |
|--------|--------|-----------|
| **PR Info** | From GitHub API | From Bitbucket API |
| **Branch Name** | `BRANCH_NAME` env var | `BITBUCKET_BRANCH` env var |
| **PR Title** | `PR_TITLE` env var | Fetched via API |
| **Comments** | GitHub REST API | Bitbucket REST API |
| **Auth** | GitHub token | Bitbucket app password |
| **Pipeline** | GitHub Actions | Bitbucket Pipelines |

**But the JIRA integration logic is identical!**

---

## 📝 **Code Changes Summary**

### **New Methods Added to `ai_code_reviewer_bitbucket.py`:**

1. `_get_pr_info()` - Fetches PR title from Bitbucket API
2. `_get_commit_messages()` - Extracts commit messages
3. `_detect_and_fetch_jira_ticket()` - Main JIRA integration
4. `_post_missing_jira_comment()` - Posts comment if no JIRA ticket
5. `_build_jira_context()` - Creates JIRA context for prompt
6. `_build_enhanced_prompt()` - Builds JIRA-aware AI prompt

### **Modified Methods:**

1. `__init__()` - Added JIRA service initialization
2. `run()` - Added JIRA detection before review
3. `review_file()` - Uses enhanced prompt with JIRA context
4. `generate_review_summary()` - Includes JIRA compliance section

---

## ✅ **Testing Checklist**

- [ ] JIRA key detection from branch name
- [ ] JIRA key detection from PR title
- [ ] JIRA key detection from commit messages
- [ ] JIRA API fetch with valid credentials
- [ ] Acceptance criteria extraction
- [ ] AI prompt includes JIRA context
- [ ] Compliance checklist generation
- [ ] Out-of-scope file detection
- [ ] PR link added to JIRA ticket
- [ ] Fallback to standard review when JIRA not configured

---

## 🎯 **Usage Example**

### **Bitbucket PR with JIRA Ticket**

**Branch:** `feature/PROJ-123-user-login`  
**PR Title:** `PROJ-123: Implement user login functionality`

**Result:**
- ✅ JIRA key detected: `PROJ-123`
- ✅ Ticket fetched from JIRA
- ✅ AI reviews against ticket requirements
- ✅ Acceptance criteria checked
- ✅ PR link added to JIRA ticket

---

## 📚 **Documentation**

For detailed setup and usage, see:
- **`JIRA_INTEGRATION_GUIDE.md`** - Complete guide (applies to both GitHub and Bitbucket)

---

## 🎉 **Status**

✅ **Bitbucket JIRA integration is complete and ready to use!**

Both GitHub and Bitbucket versions now have:
- ✅ Full JIRA integration
- ✅ Same features and capabilities
- ✅ Consistent behavior
- ✅ Backward compatible (works without JIRA config)

---

**The AI Code Review bot is now JIRA-aware on both GitHub and Bitbucket!** 🚀


