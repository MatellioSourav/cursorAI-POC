#!/usr/bin/env python3
"""
AI Code Reviewer for Bitbucket - Automated code review using OpenAI GPT
This script analyzes pull request changes and provides intelligent code review suggestions.
"""

import os
import sys
import json
import subprocess
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests
from openai import OpenAI
from jira_service import JiraService

@dataclass
class FileDiff:
    """Represents a file change in a PR"""
    filename: str
    status: str  # added, modified, deleted
    patch: str
    additions: int
    deletions: int

@dataclass
class ReviewComment:
    """Represents a code review comment"""
    file: str
    line: int
    comment: str
    severity: str  # info, warning, error

class AICodeReviewerBitbucket:
    """Main class for AI-powered code review on Bitbucket"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.bitbucket_username = os.getenv('BITBUCKET_USERNAME')
        
        # Check if BITBUCKET_USERNAME is set incorrectly
        if self.bitbucket_username and self.bitbucket_username.startswith('$'):
            print(f"❌ ERROR: BITBUCKET_USERNAME is set to literal string '{self.bitbucket_username}'")
            print("   Fix: Repository Settings → Pipelines → Repository variables")
            self.bitbucket_username = None
        
        self.bitbucket_app_password = os.getenv('BITBUCKET_APP_PASSWORD')
        
        # Validate and clean token
        if self.bitbucket_app_password:
            token_stripped = self.bitbucket_app_password.strip()
            if ' ' in token_stripped:
                print("⚠️  WARNING: Token contains spaces - authentication will fail")
            if len(token_stripped) != len(self.bitbucket_app_password):
                self.bitbucket_app_password = token_stripped
        else:
            print("❌ ERROR: BITBUCKET_APP_PASSWORD is not set")
        
        # Track which auth method works
        self._use_basic_auth = False
        self._auth_username = None
        self.workspace = os.getenv('BITBUCKET_WORKSPACE')
        self.repo_slug = os.getenv('BITBUCKET_REPO_SLUG')
        
        # Get commit info from Bitbucket environment variables
        self.base_sha = os.getenv('BITBUCKET_PR_DESTINATION_COMMIT')
        self.head_sha = os.getenv('BITBUCKET_COMMIT')
        
        # Check if we're running in PR context
        self.pr_id = os.getenv('BITBUCKET_PR_ID')
        pr_destination_branch = os.getenv('BITBUCKET_PR_DESTINATION_BRANCH')
        
        # BITBUCKET_BRANCH in PR context is the source branch (the branch being merged)
        # If BITBUCKET_BRANCH is 'qa', we might be running on qa branch directly (not a PR)
        self.branch = os.getenv('BITBUCKET_BRANCH')
        
        # Check if we're running on qa branch directly (not a PR)
        # In PR context, BITBUCKET_BRANCH is the source branch, not the destination
        is_running_on_pr = bool(self.pr_id or pr_destination_branch)
        self.is_running_on_destination_branch = self.branch == 'qa' and not is_running_on_pr
        
        if self.is_running_on_destination_branch:
            error_msg = (
                "❌ ERROR: Pipeline is running on 'qa' branch directly, not on a Pull Request.\n"
                "   This AI Code Review pipeline is designed to run ONLY on Pull Requests.\n\n"
                "   To trigger AI code review:\n"
                "   1. Create a feature branch from 'qa' (e.g., 'git checkout -b feature-branch')\n"
                "   2. Make your changes and commit\n"
                "   3. Push the branch: 'git push origin feature-branch'\n"
                "   4. Create a Pull Request: feature-branch → qa\n"
                "   5. The pipeline will run automatically on the PR\n\n"
                "   Note: The pipeline should NOT run on direct commits to 'qa' branch.\n"
                "   If you see this error on a PR, check your bitbucket-pipelines.yml configuration."
            )
            raise ValueError(error_msg)
        
        # Also check for PR-specific branch variables
        if not self.branch:
            self.branch = os.getenv('BITBUCKET_PR_SOURCE_BRANCH')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Validate API key format
        if self.openai_api_key and not self.openai_api_key.startswith('sk-'):
            print("⚠️  WARNING: OPENAI_API_KEY format appears invalid")
        
        if not self.bitbucket_app_password:
            raise ValueError("BITBUCKET_APP_PASSWORD (API Token) environment variable is required")
        
        # Strip whitespace from token (common issue)
        self.bitbucket_app_password = self.bitbucket_app_password.strip()
        
        # Detect token type
        token_preview = self.bitbucket_app_password[:4] if len(self.bitbucket_app_password) >= 4 else ""
        self.is_repository_access_token = token_preview == "ATB"  # Repository Access Token (best for inline comments)
        self.is_bitbucket_api_token = token_preview == "ATBB"  # Bitbucket API Token
        self.is_atlassian_token = token_preview == "ATAT"  # Atlassian API Token
        
        # Log token type for debugging
        if self.is_repository_access_token:
            print("✅ Repository Access Token detected (ATB...) - best for inline comments")
        elif self.is_bitbucket_api_token:
            print("ℹ️  Bitbucket API Token detected (ATBB...)")
        elif self.is_atlassian_token:
            print("⚠️  Atlassian API Token detected (ATATT...) - may not work for inline comments")
            print("   💡 For inline comments, use Repository Access Token (ATB...) instead")
            print("   Create at: Repository Settings → Access tokens")
        else:
            print(f"⚠️  Unknown token format (starts with: {token_preview}...)")
            print("   💡 For inline comments, use Repository Access Token (ATB...)")
            print("   Create at: Repository Settings → Access tokens")
        
        
        if not self.workspace or not self.repo_slug:
            raise ValueError("Bitbucket environment variables (BITBUCKET_WORKSPACE, BITBUCKET_REPO_SLUG) are required")
        
        # Bitbucket API base URL
        self.bitbucket_api_base = f"https://api.bitbucket.org/2.0/repositories/{self.workspace}/{self.repo_slug}"
        
        # Get PR ID - try environment variable first, then find via API
        self.pr_id = os.getenv('BITBUCKET_PR_ID')
        if not self.pr_id:
            # Only try to find PR if we're not running on destination branch directly
            if not self.is_running_on_destination_branch:
                print("🔍 BITBUCKET_PR_ID not set, attempting to find PR via API...")
                self.pr_id = self._find_pr_id()
                if not self.pr_id:
                    error_msg = (
                        "❌ Could not determine PR ID. Make sure:\n"
                        "1. This pipeline is running on a pull request (not on branch commits)\n"
                        "2. BITBUCKET_APP_PASSWORD contains a valid API token with required scopes\n"
                        "3. The PR is in 'Open' state\n"
                        "4. Authentication is working (check previous error messages)"
                    )
                    raise ValueError(error_msg)
            else:
                # This should have been caught earlier, but just in case
                raise ValueError("Cannot find PR ID when running on destination branch directly")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.review_comments: List[ReviewComment] = []
        
        # Initialize JIRA service
        self.jira_service = JiraService()
        self.jira_issue = None
        self.jira_key = None
        self.pr_title = None
    
    def _get_auth_headers(self, use_basic_auth=None, use_username=None, prefer_bearer=False):
        """Get authentication headers for Bitbucket API
        
        Args:
            use_basic_auth: If True, use Basic Auth. If False, use Bearer. If None, use detected method.
            use_username: Username to use for Basic Auth
            prefer_bearer: If True, prefer Bearer token (for Repository Access Tokens starting with ATB)
        """
        # Repository Access Tokens (ATB...) MUST use Bearer authentication
        if prefer_bearer or self.is_repository_access_token:
            token = self.bitbucket_app_password.strip() if self.bitbucket_app_password else ''
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        
        # Use detected auth method if not explicitly specified
        if use_basic_auth is None:
            use_basic_auth = self._use_basic_auth
        
        if use_basic_auth:
            # Basic Auth (username:token) - works with App Passwords and some Atlassian tokens
            import base64
            username = use_username or self._auth_username or self.bitbucket_username
            if not username:
                # For Atlassian tokens, try workspace or default
                username = self.workspace or 'x-token-auth'
            credentials = f"{username}:{self.bitbucket_app_password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            return {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        else:
            # Bearer token for API Tokens
            token = self.bitbucket_app_password.strip() if self.bitbucket_app_password else ''
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
    
    def _find_pr_id(self) -> Optional[str]:
        """Find PR ID by querying Bitbucket API using branch name"""
        if not self.branch:
            print("⚠️  BITBUCKET_BRANCH not set, cannot find PR")
            return None
        
        if not self.bitbucket_app_password:
            print("❌ ERROR: BITBUCKET_APP_PASSWORD is not set")
            return None
        
        try:
            test_url = f"{self.bitbucket_api_base}"
            headers = None
            
            # Try Bearer token first
            headers = self._get_auth_headers(use_basic_auth=False)
            test_response = requests.get(test_url, headers=headers, timeout=10)
            
            # If Bearer fails, try Basic Auth with different usernames
            if test_response.status_code == 401:
                token_check = self.bitbucket_app_password.strip() if self.bitbucket_app_password else ""
                
                # Try Basic Auth with username
                if self.bitbucket_username:
                    headers = self._get_auth_headers(use_basic_auth=True)
                    test_response = requests.get(test_url, headers=headers, timeout=10)
                    if test_response.status_code == 200:
                        self._use_basic_auth = True
                
                # Try with workspace
                if test_response.status_code != 200:
                    headers = self._get_auth_headers(use_basic_auth=True, use_username=self.workspace)
                    test_response = requests.get(test_url, headers=headers, timeout=10)
                    if test_response.status_code == 200:
                        self._use_basic_auth = True
                        self._auth_username = self.workspace
                
                # Try with x-token-auth (for some Atlassian tokens)
                if test_response.status_code != 200 and token_check.startswith('ATATT'):
                    headers = self._get_auth_headers(use_basic_auth=True, use_username='x-token-auth')
                    test_response = requests.get(test_url, headers=headers, timeout=10)
                    if test_response.status_code == 200:
                        self._use_basic_auth = True
                        self._auth_username = 'x-token-auth'
                
                if test_response.status_code != 200:
                    return None
            elif test_response.status_code != 200:
                return None
            
            # Get all open PRs
            prs_url = f"{self.bitbucket_api_base}/pullrequests?state=OPEN&pagelen=50"
            response = requests.get(prs_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch PRs: {response.status_code}")
                return None
            
            prs_data = response.json()
            prs = prs_data.get('values', [])
            
            # Find PR where source branch matches current branch AND destination is 'qa'
            for pr in prs:
                source_branch = pr.get('source', {}).get('branch', {}).get('name', '')
                destination_branch = pr.get('destination', {}).get('branch', {}).get('name', '')
                
                if source_branch == self.branch and destination_branch == 'qa':
                    return str(pr.get('id'))
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Network error finding PR ID: {str(e)}")
            return None
        except Exception as e:
            print(f"⚠️  Error finding PR ID: {str(e)}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def _get_commit_info_from_pr(self):
        """Get commit information from PR API if not available in environment"""
        if not self.pr_id:
            return
        
        try:
            headers = self._get_auth_headers()
            pr_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}"
            response = requests.get(pr_url, headers=headers)
            
            if response.status_code == 200:
                pr_data = response.json()
                if not self.base_sha:
                    self.base_sha = pr_data.get('destination', {}).get('commit', {}).get('hash', '')
                if not self.head_sha:
                    self.head_sha = pr_data.get('source', {}).get('commit', {}).get('hash', '')
        except Exception:
            pass
        
    def get_pr_diff(self) -> List[FileDiff]:
        """Get the diff of files changed in the PR using Bitbucket API (most accurate)"""
        # First, try to get PR diff from Bitbucket API (only includes files in PR)
        if self.pr_id:
            try:
                headers = self._get_auth_headers(prefer_bearer=True)
                diff_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}/diff"
                response = requests.get(diff_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    # Parse the diff response
                    diff_text = response.text
                    return self._parse_api_diff(diff_text)
                else:
                    print(f"⚠️  API diff failed ({response.status_code}), falling back to git diff")
            except Exception as e:
                print(f"⚠️  API diff error: {str(e)}, falling back to git diff")
        
        # Fallback: Use git diff with merge base (only changes in PR branch)
        return self._get_pr_diff_from_git()
    
    def _parse_api_diff(self, diff_text: str) -> List[FileDiff]:
        """Parse Bitbucket API diff response"""
        file_diffs = []
        current_file = None
        current_patch = []
        current_status = 'modified'
        
        for line in diff_text.split('\n'):
            # Bitbucket API diff format: "diff --git a/path/to/file b/path/to/file"
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file and current_patch:
                    patch_text = '\n'.join(current_patch)
                    additions = len([l for l in patch_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
                    deletions = len([l for l in patch_text.split('\n') if l.startswith('-') and not l.startswith('---')])
                    
                    if not self._should_skip_file(current_file):
                        file_diffs.append(FileDiff(
                            filename=current_file,
                            status=current_status,
                            patch=patch_text,
                            additions=additions,
                            deletions=deletions
                        ))
                
                # Extract filename from "diff --git a/path/to/file b/path/to/file"
                parts = line.split()
                if len(parts) >= 4:
                    filename = parts[2].replace('a/', '', 1)
                    current_file = filename
                    current_patch = [line]
                    current_status = 'modified'
                else:
                    current_file = None
            elif line.startswith('new file mode'):
                current_status = 'added'
                if current_patch:
                    current_patch.append(line)
            elif line.startswith('deleted file mode'):
                current_status = 'deleted'
                if current_patch:
                    current_patch.append(line)
            elif current_file:
                current_patch.append(line)
        
        # Save last file
        if current_file and current_patch:
            patch_text = '\n'.join(current_patch)
            additions = len([l for l in patch_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
            deletions = len([l for l in patch_text.split('\n') if l.startswith('-') and not l.startswith('---')])
            
            if not self._should_skip_file(current_file):
                file_diffs.append(FileDiff(
                    filename=current_file,
                    status=current_status,
                    patch=patch_text,
                    additions=additions,
                    deletions=deletions
                ))
        
        return file_diffs
    
    def _get_pr_diff_from_git(self) -> List[FileDiff]:
        """Fallback: Get PR diff using git (only changes in PR branch)"""
        # Verify commits exist
        if self.base_sha:
            check_base = subprocess.run(
                f"git cat-file -e {self.base_sha}",
                shell=True, capture_output=True
            )
            if check_base.returncode != 0:
                subprocess.run(f"git fetch origin {self.base_sha}", shell=True, capture_output=True)
        
        if self.head_sha:
            check_head = subprocess.run(
                f"git cat-file -e {self.head_sha}",
                shell=True, capture_output=True
            )
            if check_head.returncode != 0:
                subprocess.run(f"git fetch origin {self.head_sha}", shell=True, capture_output=True)
        
        # Use three-dot diff to get only changes in PR branch (not all changes between commits)
        # This finds the merge base and only shows changes in the PR branch
        cmd = f"git diff --name-status {self.base_sha}...{self.head_sha}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback to two-dot diff if three-dot fails
            cmd = f"git diff --name-status {self.base_sha} {self.head_sha}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise ValueError(f"Failed to get PR diff: {result.stderr}")
        
        file_diffs = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            status = parts[0]
            filename = parts[1]
            
            # Skip certain file types
            if self._should_skip_file(filename):
                continue
            
            # Get the diff for this file using three-dot diff
            diff_cmd = f"git diff {self.base_sha}...{self.head_sha} -- {filename}"
            diff_result = subprocess.run(diff_cmd, shell=True, capture_output=True, text=True)
            
            if diff_result.returncode != 0:
                # Fallback to two-dot diff
                diff_cmd = f"git diff {self.base_sha} {self.head_sha} -- {filename}"
                diff_result = subprocess.run(diff_cmd, shell=True, capture_output=True, text=True)
                if diff_result.returncode != 0:
                    continue
            
            # Count additions and deletions
            additions = len([l for l in diff_result.stdout.split('\n') if l.startswith('+') and not l.startswith('+++')])
            deletions = len([l for l in diff_result.stdout.split('\n') if l.startswith('-') and not l.startswith('---')])
            
            file_diffs.append(FileDiff(
                filename=filename,
                status=status,
                patch=diff_result.stdout,
                additions=additions,
                deletions=deletions
            ))
        
        return file_diffs
    
    def _should_skip_file(self, filename: str) -> bool:
        """Determine if a file should be skipped from review"""
        skip_patterns = [
            '.lock', 'package-lock.json', 'yarn.lock',
            '.min.js', '.min.css',
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.pdf', '.zip', '.tar', '.gz',
            'dist/', 'build/', 'node_modules/', '__pycache__/',
            '.env', '.env.local', '.env.production',
            'bitbucket-pipelines.yml', '.bitbucket/'
        ]
        
        return any(pattern in filename for pattern in skip_patterns)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension for code block syntax highlighting"""
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            # Map common extensions
            ext_map = {
                'php': 'php',
                'js': 'javascript',
                'jsx': 'javascript',
                'ts': 'typescript',
                'tsx': 'typescript',
                'py': 'python',
                'java': 'java',
                'go': 'go',
                'rs': 'rust',
                'cpp': 'cpp',
                'c': 'c',
                'cs': 'csharp',
                'rb': 'ruby',
                'sql': 'sql',
                'html': 'html',
                'css': 'css',
                'scss': 'scss',
                'json': 'json',
                'xml': 'xml',
                'yaml': 'yaml',
                'yml': 'yaml'
            }
            return ext_map.get(ext, ext)
        return 'text'
    
    def _get_code_snippet(self, filepath: str, line_number: int, context_lines: int = 3) -> Optional[str]:
        """Extract code snippet around a specific line"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if line_number < 1 or line_number > len(lines):
                return None
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            snippet_lines = []
            for i in range(start, end):
                line_num = i + 1
                prefix = ">>> " if line_num == line_number else "    "
                snippet_lines.append(f"{prefix}Line {line_num:04d}: {lines[i]}")
            
            return "".join(snippet_lines)
        except:
            return None
    
    def _validate_line_number(self, filepath: str, line_number: int) -> bool:
        """Validate that a line number exists in the file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return 1 <= line_number <= len(lines)
        except:
            return False
    
    def _build_enhanced_prompt(self, file_diff: FileDiff, file_content: str) -> str:
        """Build AI prompt with JIRA context if available"""
        jira_context = self._build_jira_context()
        
        # Get list of all changed files for scope check
        file_diffs = getattr(self, '_all_file_diffs', [])
        changed_files = [fd.filename for fd in file_diffs]
        
        # Build base prompt
        base_prompt = f"""You are a strict code-review agent.

{jira_context if jira_context else ""}

## CODE CHANGES

**File:** {file_diff.filename}
**Status:** {file_diff.status}
**Changes:** +{file_diff.additions} -{file_diff.deletions}

**All Changed Files in PR:**
{chr(10).join(f"- {f}" for f in changed_files)}

**DIFF:**
{file_diff.patch}

**FULL FILE CONTENT (for context only - focus on DIFF changes):**
{file_content[:5000]}

"""
        
        # Add JIRA-specific requirements if JIRA ticket is available
        if self.jira_issue:
            subtasks = self.jira_issue.get('subtasks', [])
            has_subtasks = len(subtasks) > 0
            
            base_prompt += f"""
**CRITICAL: This code must be evaluated against JIRA ticket {self.jira_key}**

1. **Requirement Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches JIRA description
   - ✅ Check all acceptance criteria are met
   - ❌ Flag any missing acceptance criteria
   - ❌ Flag any out-of-scope changes
   - ⚠️  Highlight files changed that are unrelated to JIRA scope

2. **Scope Validation**:
   - Review if ALL changed files are relevant to JIRA ticket {self.jira_key}
   - Flag any files that seem unrelated to the ticket requirements
   - Ensure no accidental changes to unrelated functionality

3. **Acceptance Criteria Checklist**:
   - Create a checklist showing which acceptance criteria are met
   - Clearly mark any missing or incomplete criteria
   - Provide specific line references where criteria are implemented
   - Treat description as the primary source of acceptance criteria

"""
            
            # Add subtask coverage if subtasks exist
            if has_subtasks:
                base_prompt += f"""4. **Subtask Coverage** (🧾):
   - Verify implementation covers ALL subtasks:
"""
                for subtask in subtasks:
                    subtask_key = subtask.get('key', '')
                    subtask_summary = subtask.get('summary', '')
                    base_prompt += f"     - **{subtask_key}**: {subtask_summary}\n"
                base_prompt += """   - Check if each subtask requirement is addressed in the code
   - Flag any subtasks that are not implemented
   - Provide evidence of subtask implementation (file/line references)

"""
                base_prompt += """5. **Testing Requirements**:
"""
            else:
                base_prompt += """4. **Testing Requirements**:
"""
            
            base_prompt += """   - If business logic changed and no tests were added: ⚠️ WARN explicitly
   - Verify test coverage for new functionality
   - Check if acceptance criteria are testable
   - Apply stricter validation if JIRA summary or subtasks imply backend-critical changes

6. **Quality Enforcement**:
   - Warn if files changed are not aligned with JIRA scope
   - Flag business logic changes without corresponding tests
   - Apply stricter checks for critical backend changes

"""
        
        base_prompt += """Your job: Identify ONLY **Critical** and **High-severity** issues in the changed code of this pull request.  
Ignore everything else.

⚠️ Report an issue ONLY if it:
- Introduces a security vulnerability
- Can break the application
- Causes data loss or corruption
- Creates major performance degradation
- Violates essential best practices that will cause bugs
- Breaks architecture, API contracts, or business logic
- **Does NOT meet JIRA ticket requirements** (if JIRA ticket provided)
- **Missing acceptance criteria** (if JIRA ticket provided)
- **Out-of-scope changes** (if JIRA ticket provided)

❌ Do NOT report:
- Low/medium severity issues
- Style, formatting, naming, or cosmetic suggestions
- Minor optimizations
- Unnecessary code rewrites
- Long explanations or subjective opinions

IMPORTANT: 
- Only review code that appears in the DIFF section above
- Line numbers in your response must refer to the actual line numbers in the current file
- Double-check the line numbers against the FULL FILE CONTENT before responding
- If you mention a line number, verify it exists in the file and contains the code you're referencing
- Provide code snippets from the actual file content to match your line numbers

🟦 For EACH valid finding, respond in this exact format:
[Severity: Critical/High]
Issue: <1–2 sentence explanation>
Fix: <correct, minimal code snippet>
File: <file name>
Line: <line numbers>

Format your response as JSON with the following structure:
{{
  "overall_assessment": "Brief summary - only mention if Critical/High issues found",
  "jira_compliance": {{
    "matches_requirements": true/false,
    "missing_criteria": ["List of missing acceptance criteria"],
    "out_of_scope_files": ["List of files not related to JIRA ticket"],
    "acceptance_criteria_checklist": [
      {{"criteria": "Criterion text", "status": "✅ Met | ❌ Missing | ⚠️ Partial", "evidence": "Line references"}}
    ],
    "subtask_coverage": [
      {{"subtask_key": "H30-XXXXX", "status": "✅ Covered | ❌ Missing | ⚠️ Partial", "evidence": "File/line references"}}
    ],
    "final_verdict": "Approve | Changes Requested"
  }},
  "issues": [
    {{
      "line": <line_number - MUST be accurate line number from the file>,
      "severity": "critical|error",
      "category": "requirement|scope|security|bug|performance|architecture",
      "title": "Brief issue title (1-5 words)",
      "description": "1-2 sentence explanation",
      "suggestion": "Correct, minimal, executable code snippet fixing ONLY this issue"
    }}
  ]
}}

**IMPORTANT:**
- If acceptance criteria are missing or violated, mark severity as "error" and set final_verdict to "Changes Requested"
- If files are out of scope, create issues with category "scope"
- If subtasks are not covered, mark them as "❌ Missing" in subtask_coverage
- Be specific about which acceptance criteria are met/missing
- Provide line references for requirement implementation
- If business logic changed without tests, create a "testing" issue with severity "error"
- Set final_verdict to "Changes Requested" if any requirements are missing or incorrect
- Set final_verdict to "Approve" only if all requirements are met

**OUTPUT FORMAT (Strict Markdown Structure):**
Your response must include these sections in markdown:
- ✅ Matches JIRA Requirements
- ❌ Missing / Incorrect Implementation  
- ⚠️ Suggestions / Improvements
- 📋 Acceptance Criteria Checklist
- 🧾 Subtask Coverage (if subtasks exist)
- 🔚 Final Verdict (Approve / Changes Requested)

If there are **no Critical or High issues**, respond with:
{{
  "overall_assessment": "No critical or high-severity issues found",
  "jira_compliance": {{
    "matches_requirements": true, 
    "missing_criteria": [], 
    "out_of_scope_files": [],
    "subtask_coverage": [],
    "final_verdict": "Approve"
  }},
  "issues": []
}}

Be strict. Only report issues that will cause real problems. Verify all line numbers are correct."""
        
        return base_prompt
    
    def review_file(self, file_diff: FileDiff) -> Optional[Dict]:
        """Review a single file using AI"""
        print(f"📝 Reviewing {file_diff.filename}...")
        
        # Read the full file content if it exists
        try:
            with open(file_diff.filename, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except:
            file_content = "File not accessible or was deleted"
        
        # Build enhanced prompt with JIRA context
        prompt = self._build_enhanced_prompt(file_diff, file_content)

        try:
            # Enhanced system message for JIRA-aware reviews
            system_message = "You are a strict code-review agent. You identify ONLY Critical and High-severity issues that will cause security vulnerabilities, break the application, cause data loss, or create major performance problems. You ignore style, formatting, naming, minor optimizations, and low-severity issues. You always verify line numbers are accurate and provide only correct, executable code snippets."
            if self.jira_issue:
                system_message += " You are also an expert at evaluating code implementations against JIRA ticket requirements and acceptance criteria. You must strictly verify that code changes align with the specified requirements."
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            review_result = json.loads(response.choices[0].message.content)
            return review_result
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ Error reviewing {file_diff.filename}: {error_str}")
            
            # Check for API key errors and provide helpful guidance
            if 'invalid_api_key' in error_str or 'Incorrect API key' in error_str or '401' in error_str:
                print("")
                print("🔑 OpenAI API Key Error Detected!")
                print("   Your OPENAI_API_KEY appears to be invalid.")
                print("   Valid OpenAI API keys:")
                print("   - Start with 'sk-' or 'sk-proj-'")
                print("   - Are about 50-60 characters long")
                print("   - Come from: https://platform.openai.com/account/api-keys")
                print("")
                print("   To fix:")
                print("   1. Go to: https://platform.openai.com/account/api-keys")
                print("   2. Create a new API key (starts with 'sk-')")
                print("   3. Update OPENAI_API_KEY in Bitbucket:")
                print("      Repository Settings → Pipelines → Repository variables")
                print("   4. Make sure your OpenAI account has credits/billing set up")
                print("")
            
            return None
    
    def _delete_previous_ai_comments(self):
        """Delete previous AI review comments to prevent email spam"""
        try:
            comments_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}/comments"
            headers = self._get_auth_headers()
            response = requests.get(comments_url, headers=headers)
            
            if response.status_code == 200:
                comments_data = response.json()
                comments = comments_data.get('values', [])
                
                for comment in comments:
                    content = comment.get('content', {}).get('raw', '')
                    if '🤖 Generated by AI Code Reviewer' in content or '🤖 AI Code Review Summary' in content:
                        comment_id = comment.get('id')
                        if comment_id:
                            delete_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}/comments/{comment_id}"
                            requests.delete(delete_url, headers=headers)
        except Exception:
            pass
    
    def _delete_previous_summary_comment(self):
        """Delete previous summary comment (handled in _delete_previous_ai_comments)"""
        pass
    
    def post_review_comments(self, file_diff: FileDiff, review: Dict):
        """Post review comments to Bitbucket PR"""
        if not review or not review.get('issues'):
            return
        
        # Bitbucket API endpoint for PR comments
        comments_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}/comments"
        
        # For inline comments, Repository Access Tokens (ATB...) work best
        # Always prefer Bearer token for inline comments
        headers = self._get_auth_headers(prefer_bearer=True)
        
        # If Repository Access Token detected, use Bearer auth
        if self.is_repository_access_token:
            # Repository Access Tokens MUST use Bearer authentication
            pass  # Already set above
        elif not headers:
            # Fallback: try Basic Auth if Bearer fails
            try:
                if self.bitbucket_username:
                    headers = self._get_auth_headers(use_basic_auth=True)
                elif self.workspace:
                    headers = self._get_auth_headers(use_basic_auth=True, use_username=self.workspace)
                else:
                    headers = self._get_auth_headers(use_basic_auth=True, use_username='x-token-auth')
            except Exception:
                pass
        
        if not headers:
            raise Exception("Could not get authentication headers")
        
        for issue in review['issues']:
            # Only process Critical and High-severity issues
            issue_severity = issue.get('severity', '').lower()
            if issue_severity not in ['critical', 'error', 'high']:
                continue  # Skip low/medium severity issues
            
            # Create comment body
            emoji_map = {
                'security': '🔒',
                'bug': '🐛',
                'performance': '⚡',
                'architecture': '🏗️'
            }
            
            severity_emoji = {
                'critical': '🔴',
                'error': '🔴',
                'high': '🔴'
            }
            
            emoji = emoji_map.get(issue.get('category', ''), '🔴')
            severity = severity_emoji.get(issue_severity, '🔴')
            
            line_number = issue.get('line')
            line_valid = False
            code_snippet = None
            
            if line_number and isinstance(line_number, int):
                line_valid = self._validate_line_number(file_diff.filename, line_number)
                if line_valid:
                    code_snippet = self._get_code_snippet(file_diff.filename, line_number)
            
            # Format: [Severity: Critical/High] Issue: <explanation> Fix: <code>
            comment_body = f"""{severity} **[Severity: {issue_severity.upper()}]** {emoji}

**Issue**: {issue['description']}

**Fix**:
```{self._get_file_extension(file_diff.filename)}
{issue.get('suggestion', 'No fix provided')}
```

**File**: `{file_diff.filename}`  
**Line**: {line_number if line_number else 'N/A'}"""

            comment_body += "\n\n---\n*🤖 Generated by AI Code Reviewer - Critical/High Issues Only*"
            
            if line_number and line_valid:
                # Post as inline comment on specific line
                comment_data = {
                    'content': {
                        'raw': comment_body
                    },
                    'inline': {
                        'to': line_number,
                        'path': file_diff.filename
                    }
                }
                
                try:
                    response = requests.post(
                        comments_url,
                        headers=headers,
                        json=comment_data
                    )
                    if response.status_code in [200, 201]:
                        print(f"✅ Posted inline comment on {file_diff.filename}:{line_number}")
                    elif response.status_code == 401:
                        error_text = response.text[:200] if response.text else ""
                        if "Repository Access Token" in error_text or not self.is_repository_access_token:
                            print(f"⚠️  Inline comment auth failed - Repository Access Token (ATB...) required for inline comments")
                            print(f"   Current token type: {self.bitbucket_app_password[:4]}...")
                            print(f"   Create Repository Access Token: Repository Settings → Access tokens")
                        
                        # Try posting as regular comment (non-inline) as fallback
                        regular_comment_data = {
                            'content': {'raw': comment_body}
                        }
                        try:
                            regular_response = requests.post(comments_url, headers=headers, json=regular_comment_data)
                            if regular_response.status_code in [200, 201]:
                                print(f"✅ Posted as regular comment on {file_diff.filename}")
                            else:
                                # Store for summary
                                self.review_comments.append(ReviewComment(
                                    file=file_diff.filename,
                                    line=line_number or 0,
                                    comment=comment_body,
                                    severity=issue.get('severity', 'info')
                                ))
                        except Exception:
                            # Store for summary
                            self.review_comments.append(ReviewComment(
                                file=file_diff.filename,
                                line=line_number or 0,
                                comment=comment_body,
                                severity=issue.get('severity', 'info')
                            ))
                    else:
                        # Store for summary
                        self.review_comments.append(ReviewComment(
                            file=file_diff.filename,
                            line=line_number or 0,
                            comment=comment_body,
                            severity=issue.get('severity', 'info')
                        ))
                except Exception:
                    # Store for summary
                    self.review_comments.append(ReviewComment(
                        file=file_diff.filename,
                        line=line_number or 0,
                        comment=comment_body,
                        severity=issue.get('severity', 'info')
                    ))
            else:
                # Store for summary comment
                note = "Line could not be matched precisely; including in summary instead."
                comment_body += f"\n_{note}_\n"
                self.review_comments.append(ReviewComment(
                    file=file_diff.filename,
                    line=line_number or 0,
                    comment=comment_body,
                    severity=issue.get('severity', 'info')
                ))
    
    def generate_review_summary(self, file_reviews: List[tuple]):
        """Generate a summary of the entire review"""
        print("📊 Generating review summary...")
        
        total_files = len(file_reviews)
        total_issues = sum(len(review.get('issues', [])) for _, review in file_reviews if review)
        
        # Only count Critical and High-severity issues
        critical_count = sum(
            1 for _, review in file_reviews if review 
            for issue in review.get('issues', []) 
            if issue.get('severity', '').lower() in ['critical', 'error', 'high']
        )
        
        summary = f"""# 🤖 AI Code Review Summary"""
        
        # Add JIRA context if available
        if self.jira_issue:
            subtasks = self.jira_issue.get('subtasks', [])
            subtasks_info = ""
            if subtasks:
                subtasks_info = f"\n**Subtasks:** {len(subtasks)} subtask(s)"
            
            summary += f"""

## 🎫 JIRA Ticket: [{self.jira_key}]({self.jira_issue.get('url', '')})

**Summary:** {self.jira_issue.get('summary', 'N/A')}{subtasks_info}

"""
        
        summary += f"""
## Overview
- **Files Reviewed**: {total_files}
- **Critical/High Issues Found**: {critical_count}

"""
        
        # Add JIRA compliance section if available
        if self.jira_issue:
            summary += "## 📋 JIRA Compliance Check\n\n"
            
            all_compliant = True
            for _, review in file_reviews:
                if not review:
                    continue
                
                jira_compliance = review.get('jira_compliance', {})
                matches = jira_compliance.get('matches_requirements', False)
                missing = jira_compliance.get('missing_criteria', [])
                out_of_scope = jira_compliance.get('out_of_scope_files', [])
                checklist = jira_compliance.get('acceptance_criteria_checklist', [])
                subtask_coverage = jira_compliance.get('subtask_coverage', [])
                final_verdict = jira_compliance.get('final_verdict', '')
                
                if not matches or missing or out_of_scope:
                    all_compliant = False
                
                # Check subtask coverage
                if subtask_coverage:
                    missing_subtasks = [st for st in subtask_coverage if 'missing' in st.get('status', '').lower()]
                    if missing_subtasks:
                        all_compliant = False
                
                # Final verdict section
                if final_verdict:
                    verdict_emoji = "✅" if "approve" in final_verdict.lower() else "❌"
                    summary += f"### 🔚 Final Verdict\n\n"
                    summary += f"{verdict_emoji} **{final_verdict}**\n\n"
                
                # Acceptance Criteria Checklist
                if checklist:
                    summary += "### 📋 Acceptance Criteria Checklist\n\n"
                    for item in checklist:
                        summary += f"{item.get('status', '❓')} {item.get('criteria', 'N/A')}\n"
                        if item.get('evidence'):
                            summary += f"   *Evidence: {item.get('evidence')}*\n"
                    summary += "\n"
                
                # Subtask Coverage
                if subtask_coverage:
                    summary += "### 🧾 Subtask Coverage\n\n"
                    for subtask in subtask_coverage:
                        subtask_key = subtask.get('subtask_key', 'N/A')
                        subtask_status = subtask.get('status', '❓')
                        subtask_evidence = subtask.get('evidence', '')
                        summary += f"{subtask_status} **{subtask_key}**\n"
                        if subtask_evidence:
                            summary += f"   *Evidence: {subtask_evidence}*\n"
                    summary += "\n"
                
                if missing:
                    summary += "### ❌ Missing Acceptance Criteria\n\n"
                    for criteria in missing:
                        summary += f"- {criteria}\n"
                    summary += "\n"
                
                if out_of_scope:
                    summary += "### ⚠️ Out-of-Scope Files\n\n"
                    summary += "The following files appear unrelated to JIRA ticket requirements:\n\n"
                    for file in out_of_scope:
                        summary += f"- `{file}`\n"
                    summary += "\n"
            
            if all_compliant:
                summary += "✅ **All JIRA requirements appear to be met!**\n\n"
            else:
                summary += "❌ **Some JIRA requirements are not met. Please review.**\n\n"
            
            summary += "---\n\n"
        
        summary += "## Detailed Analysis\n\n"
        
        for file_diff, review in file_reviews:
            if not review:
                continue
            
            # Only show Critical and High-severity issues
            critical_issues = [i for i in review.get('issues', []) 
                             if i.get('severity', '').lower() in ['critical', 'error', 'high']]
            
            if not critical_issues:
                continue  # Skip files with no critical issues
            
            summary += f"\n### 📄 `{file_diff.filename}`\n\n"
            summary += f"**Critical/High Issues Found**: {len(critical_issues)}\n\n"
                
            for i, issue in enumerate(critical_issues, 1):
                emoji_map = {
                    'security': '🔒',
                    'bug': '🐛',
                    'performance': '⚡',
                    'architecture': '🏗️'
                }
                emoji = emoji_map.get(issue.get('category', ''), '🔴')
                severity = issue.get('severity', 'critical').upper()
                
                summary += f"{i}. {emoji} **[Severity: {severity}]** {issue['title']}\n"
                summary += f"   - **File**: `{file_diff.filename}`\n"
                summary += f"   - **Line**: {issue.get('line', 'N/A')}\n"
                summary += f"   - **Issue**: {issue['description']}\n"
                if issue.get('suggestion'):
                    summary += f"   - **Fix**:\n```{self._get_file_extension(file_diff.filename)}\n{issue['suggestion']}\n```\n"
                summary += "\n"
        
        if critical_count == 0:
            summary += "\n✅ **No Critical or High-severity issues found.**\n"
        
        summary += "\n---\n"
        summary += "*🤖 Generated by AI Code Reviewer - Critical/High Issues Only*\n"
        
        # Save summary to file
        with open('review_summary.md', 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print("✅ Review summary saved to review_summary.md")
    
    def _validate_authentication_early(self) -> bool:
        """Validate authentication - tries multiple auth methods, non-blocking"""
        test_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}"
        token_check = self.bitbucket_app_password.strip() if self.bitbucket_app_password else ""
        
        # Try Bearer token first (for API tokens)
        try:
            headers = self._get_auth_headers(use_basic_auth=False)
            response = requests.get(test_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                return True
        except Exception:
            pass
        
        # If Bearer fails and token is Atlassian (ATATT...), try Basic Auth
        if token_check.startswith('ATATT'):
            # Try with username
            if self.bitbucket_username:
                try:
                    headers = self._get_auth_headers(use_basic_auth=True)
                    response = requests.get(test_url, headers=headers, timeout=5)
                    
                    if response.status_code == 200:
                        self._use_basic_auth = True
                        return True
                except Exception:
                    pass
            
            # Try with workspace as username
            try:
                headers = self._get_auth_headers(use_basic_auth=True, use_username=self.workspace)
                response = requests.get(test_url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    self._use_basic_auth = True
                    self._auth_username = self.workspace
                    return True
            except Exception:
                pass
            
            # Try with 'x-token-auth' as username (some Atlassian tokens use this)
            try:
                headers = self._get_auth_headers(use_basic_auth=True, use_username='x-token-auth')
                response = requests.get(test_url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    self._use_basic_auth = True
                    self._auth_username = 'x-token-auth'
                    return True
            except Exception:
                pass
        
        # Could not validate, but continue anyway - will fail during actual operations if invalid
        return False
    
    def _get_pr_info(self):
        """Fetch PR title from Bitbucket API"""
        if self.pr_title:
            return
        
        try:
            pr_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}"
            headers = self._get_auth_headers(prefer_bearer=True)
            response = requests.get(pr_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pr_data = response.json()
                self.pr_title = pr_data.get('title', '')
                print(f"📋 PR Title: {self.pr_title}")
        except Exception as e:
            print(f"⚠️  Could not fetch PR info: {str(e)}")
    
    def _get_commit_messages(self) -> List[str]:
        """Get commit messages from the PR"""
        try:
            cmd = f"git log {self.base_sha}..{self.head_sha} --pretty=format:%s"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            commits = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return commits[:10]  # Limit to last 10 commits
        except Exception as e:
            print(f"⚠️  Could not fetch commit messages: {str(e)}")
            return []
    
    def _detect_and_fetch_jira_ticket(self) -> bool:
        """
        Detect JIRA ticket and fetch details
        
        Returns:
            True if JIRA ticket found and fetched, False otherwise
        """
        if not self.jira_service.enabled:
            print("ℹ️  JIRA integration not configured, proceeding with standard review")
            return False
        
        # Get commit messages
        commit_messages = self._get_commit_messages()
        
        # Find JIRA key
        self.jira_key = self.jira_service.find_jira_key(
            self.branch or '', 
            self.pr_title or '', 
            commit_messages
        )
        
        if not self.jira_key:
            # Post comment asking for JIRA ticket
            self._post_missing_jira_comment()
            return False
        
        # Fetch JIRA issue details
        self.jira_issue = self.jira_service.fetch_issue(self.jira_key)
        
        if not self.jira_issue:
            print(f"⚠️  Could not fetch JIRA issue {self.jira_key}, proceeding with standard review")
            return False
        
        print(f"✅ JIRA Issue Found: {self.jira_key}")
        print(f"   Summary: {self.jira_issue.get('summary', 'N/A')}")
        print(f"   Type: {self.jira_issue.get('issue_type', 'N/A')}")
        return True
    
    def _post_missing_jira_comment(self):
        """Post comment asking for JIRA ticket"""
        comment_body = """## ⚠️ JIRA Ticket Required

This PR does not have a linked JIRA ticket. Please add a JIRA ticket key to:

- **PR Title** (e.g., `PROJ-123: Add login feature`)
- **Branch Name** (e.g., `feature/PROJ-123-login`)
- **Commit Message** (e.g., `PROJ-123: Implement login`)

**JIRA Key Format:** `[A-Z][A-Z0-9]+-[0-9]+` (e.g., `PROJ-123`, `ABC-456`)

Once a valid JIRA ticket is detected, the AI review will evaluate your code against the ticket's requirements and acceptance criteria.

---
*🤖 Generated by AI Code Reviewer*
"""
        
        try:
            comments_url = f"{self.bitbucket_api_base}/pullrequests/{self.pr_id}/comments"
            headers = self._get_auth_headers(prefer_bearer=True)
            response = requests.post(comments_url, headers=headers, json={'content': {'raw': comment_body}}, timeout=10)
            
            if response.status_code in [200, 201]:
                print("📝 Posted comment requesting JIRA ticket")
            else:
                print(f"⚠️  Could not post JIRA request comment: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Exception posting JIRA request: {str(e)}")
    
    def _build_jira_context(self) -> str:
        """Build JIRA context string for AI prompt"""
        if not self.jira_issue:
            return ""
        
        # Build subtasks section if present
        subtasks = self.jira_issue.get('subtasks', [])
        subtasks_section = ""
        if subtasks:
            subtasks_section = "\n**Subtasks:**\n"
            for subtask in subtasks:
                subtask_key = subtask.get('key', 'N/A')
                subtask_summary = subtask.get('summary', 'N/A')
                subtasks_section += f"- **{subtask_key}**: {subtask_summary}\n"
        
        context = f"""
## JIRA TICKET CONTEXT

**JIRA Issue:** {self.jira_key}
**Summary:** {self.jira_issue.get('summary', 'N/A')}
{subtasks_section}
**Description:**
{self.jira_issue.get('description', 'No description provided')}

**Acceptance Criteria:**
{self.jira_issue.get('acceptance_criteria', 'No acceptance criteria specified')}

**JIRA Link:** {self.jira_issue.get('url', '')}

---
"""
        return context
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting AI Code Review...")
        print(f"📦 Repository: {self.workspace}/{self.repo_slug}")
        print(f"🔀 PR #{self.pr_id}")
        print(f"📊 Comparing {self.base_sha[:7]} → {self.head_sha[:7]}")
        print("-" * 60)
        
        # Try to validate authentication (non-blocking - will fail during actual operations if invalid)
        self._validate_authentication_early()
        
        # Get PR info (title)
        self._get_pr_info()
        
        # Detect and fetch JIRA ticket
        if self.jira_service.enabled:
            print("🔍 JIRA integration enabled - checking for JIRA ticket...")
            jira_available = self._detect_and_fetch_jira_ticket()
            
            if not jira_available:
                print("⏭️  Skipping AI review - JIRA ticket required")
                return
            else:
                print(f"✅ JIRA ticket {self.jira_key} found - proceeding with JIRA-aware review")
        else:
            print("ℹ️  JIRA integration not configured - proceeding with standard review")
        
        # Delete previous AI comments
        self._delete_previous_ai_comments()
        self._delete_previous_summary_comment()
        
        # Validate we have the necessary commit SHAs
        if not self.base_sha or not self.head_sha:
            self._get_commit_info_from_pr()
        
        if not self.base_sha or not self.head_sha:
            raise ValueError("Could not determine base and head commits. BITBUCKET_PR_DESTINATION_COMMIT and BITBUCKET_COMMIT are required.")
        
        # Get PR diff
        file_diffs = self.get_pr_diff()
        
        if not file_diffs:
            print("ℹ️  No files to review")
            return
        
        print(f"📁 Found {len(file_diffs)} file(s) to review")
        print("-" * 60)
        
        # Store file_diffs for use in prompt building
        self._all_file_diffs = file_diffs
        
        # Review each file
        file_reviews = []
        comment_errors = 0
        for file_diff in file_diffs:
            try:
                review = self.review_file(file_diff)
                if review:
                    file_reviews.append((file_diff, review))
                    try:
                        self.post_review_comments(file_diff, review)
                    except Exception as e:
                        comment_errors += 1
                        print(f"⚠️  Failed to post comments for {file_diff.filename}: {str(e)}")
            except Exception as e:
                print(f"⚠️  Error reviewing {file_diff.filename}: {str(e)}")
                continue
        
        # Generate summary (always generate, even if comments failed)
        try:
            self.generate_review_summary(file_reviews)
        except Exception as e:
            print(f"⚠️  Failed to generate summary: {str(e)}")
        
        # Add PR link to JIRA ticket (optional)
        if self.jira_issue and self.jira_key:
            pr_url = f"https://bitbucket.org/{self.workspace}/{self.repo_slug}/pull-requests/{self.pr_id}"
            self.jira_service.add_pr_comment(self.jira_key, pr_url, self.pr_title or '')
        
        print("-" * 60)
        if comment_errors > 0:
            print(f"⚠️  AI Code Review Complete with {comment_errors} comment posting error(s)")
            print(f"📝 Reviewed {len(file_reviews)} files")
            print(f"💬 Summary saved to review_summary.md (comments may not have been posted)")
        else:
            print("✅ AI Code Review Complete!")
            print(f"📝 Reviewed {len(file_reviews)} files")
            print(f"💬 Check the PR for detailed comments and suggestions")

if __name__ == "__main__":
    try:
        reviewer = AICodeReviewerBitbucket()
        reviewer.run()
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

