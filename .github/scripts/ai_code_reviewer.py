#!/usr/bin/env python3
"""
AI Code Reviewer - Automated code review using OpenAI GPT
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
from srs_service import SRSService

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

class AICodeReviewer:
    """Main class for AI-powered code review"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.pr_number = os.getenv('PR_NUMBER')
        self.repo_name = os.getenv('REPO_NAME')
        self.base_sha = os.getenv('BASE_SHA')
        self.head_sha = os.getenv('HEAD_SHA')
        self.pr_title = os.getenv('PR_TITLE', '')
        self.branch_name = os.getenv('BRANCH_NAME', '')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client with timeout (120 seconds for large prompts)
        self.client = OpenAI(api_key=self.openai_api_key, timeout=120.0)
        self.review_comments: List[ReviewComment] = []
        
        # Initialize JIRA service
        self.jira_service = JiraService()
        self.jira_issue = None
        self.jira_key = None
        
        # Initialize SRS service
        self.srs_service = SRSService()
        self.srs_context = None
        
    def get_pr_diff(self) -> List[FileDiff]:
        """Get the diff of files changed in the PR"""
        print("🔍 Fetching PR changes...")
        
        # Get list of changed files
        cmd = f"git diff --name-status {self.base_sha} {self.head_sha}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Debug: Check git diff result
        if result.returncode != 0:
            print(f"⚠️  Error running git diff: {result.stderr}")
            print(f"   Command: {cmd}")
            return []
        
        if not result.stdout.strip():
            print(f"⚠️  No files found in git diff between {self.base_sha[:7]} and {self.head_sha[:7]}")
            return []
        
        print(f"📋 Found {len(result.stdout.strip().split())} file change(s) in git diff")
        
        # Get files that were changed in commits with current JIRA key (if available)
        files_from_jira_commits = set()
        if self.jira_key:
            print(f"🔍 Filtering files from commits with JIRA key {self.jira_key}...")
            # Get commits between base and head that contain the JIRA key in commit message
            commit_cmd = f"git log {self.base_sha}..{self.head_sha} --pretty=format:%H --grep={self.jira_key} --all-match"
            commit_result = subprocess.run(commit_cmd, shell=True, capture_output=True, text=True)
            
            if commit_result.stdout.strip():
                commit_hashes = commit_result.stdout.strip().split('\n')
                print(f"📝 Found {len(commit_hashes)} commit(s) with JIRA key {self.jira_key}")
                
                # Get files changed in those commits
                for commit_hash in commit_hashes:
                    file_cmd = f"git diff-tree --no-commit-id --name-only -r {commit_hash}"
                    file_result = subprocess.run(file_cmd, shell=True, capture_output=True, text=True)
                    for file in file_result.stdout.strip().split('\n'):
                        if file:
                            files_from_jira_commits.add(file)
                
                if files_from_jira_commits:
                    print(f"✅ Will review {len(files_from_jira_commits)} file(s) from commits with JIRA key {self.jira_key}")
            else:
                # If no commits found with JIRA key, check if branch name or PR title has it
                # In that case, review all files (might be first commit without JIRA key in message)
                print(f"⚠️  No commits found with JIRA key {self.jira_key} in commit message")
                print(f"   Reviewing all files in PR (JIRA key found in branch/PR title)")
        
        file_diffs = []
        lines = result.stdout.strip().split('\n')
        print(f"📋 Processing {len(lines)} file change(s) from git diff")
        
        for line in lines:
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            status = parts[0]
            filename = parts[1]
            
            print(f"   Checking: {filename} (status: {status})")
            
            # Skip certain file types
            if self._should_skip_file(filename):
                print(f"   ⏭️  Skipping {filename} (matches skip patterns)")
                continue
            
            # If JIRA key is available, only review files from commits with that JIRA key
            if self.jira_key:
                if files_from_jira_commits:
                    # We have commits with JIRA key - only review files from those commits
                    if filename not in files_from_jira_commits:
                        print(f"⏭️  Skipping {filename} (not in commits with JIRA key {self.jira_key})")
                        continue
                else:
                    # No commits found with JIRA key, but JIRA key exists in branch/PR
                    # Only review files that match the JIRA ticket context
                    # For SEC-400 (payment), only review payment-related files
                    if not self._is_file_related_to_jira_ticket(filename):
                        print(f"⏭️  Skipping {filename} (not related to JIRA ticket {self.jira_key})")
                        continue
            
            # Get the diff for this file
            diff_cmd = f"git diff {self.base_sha} {self.head_sha} -- {filename}"
            diff_result = subprocess.run(diff_cmd, shell=True, capture_output=True, text=True)
            
            # Only include if there are actual changes (not just whitespace)
            if not diff_result.stdout.strip() or diff_result.stdout.strip() == '':
                print(f"   ⏭️  Skipping {filename} (empty diff)")
                continue
            
            # Count additions and deletions
            additions = len([l for l in diff_result.stdout.split('\n') if l.startswith('+') and not l.startswith('+++')])
            deletions = len([l for l in diff_result.stdout.split('\n') if l.startswith('-') and not l.startswith('---')])
            
            # Skip if no actual code changes (only metadata)
            if additions == 0 and deletions == 0:
                print(f"   ⏭️  Skipping {filename} (no additions or deletions)")
                continue
            
            print(f"   ✅ Including {filename} (+{additions} -{deletions})")
            file_diffs.append(FileDiff(
                filename=filename,
                status=status,
                patch=diff_result.stdout,
                additions=additions,
                deletions=deletions
            ))
        
        print(f"📊 Final review list: {len(file_diffs)} file(s) to review")
        return file_diffs
    
    def _should_skip_file(self, filename: str) -> bool:
        """Determine if a file should be skipped from review"""
        # Always skip these patterns (infrastructure, config, docs, etc.)
        always_skip_patterns = [
            # Lock files
            '.lock', 'package-lock.json', 'yarn.lock',
            # Minified files
            '.min.js', '.min.css',
            # Binary files
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
            '.pdf', '.zip', '.tar', '.gz', '.rar',
            # Build/dist directories
            'dist/', 'build/', 'node_modules/', '__pycache__/', '.next/', 'out/',
            # Environment files
            '.env', '.env.local', '.env.production', '.env.development',
            # CI/CD configuration files (not part of feature code)
            '.github/', '.gitlab-ci.yml', 'bitbucket-pipelines.yml', '.circleci/',
            # IDE files
            '.idea/', '.vscode/', '.settings/',
            # Temporary files
            '.tmp', '.temp', '.log', '.cache',
        ]
        
        # Skip if matches always-skip patterns
        if any(pattern in filename for pattern in always_skip_patterns):
            return True
        
        # Skip documentation files (unless in src/ or feature directories)
        doc_patterns = ['.md', 'README', 'CHANGELOG', 'LICENSE', 'CONTRIBUTING', 'SETUP', 'QUICK_START']
        if any(pattern in filename for pattern in doc_patterns):
            # Only review docs if they're in src/ or feature directories
            if not any(dir in filename for dir in ['src/', 'lib/', 'app/', 'features/', 'docs/']):
                return True
        
        # Skip demo/example files (always skip, they're not production code)
        filename_lower = filename.lower()
        demo_patterns = [
            'demo_', 'demo.', 'demo-', '/demo/',
            'example_', 'example.', 'example-', '/example/',
            'sample_', 'sample.', 'sample-', '/sample/'
        ]
        if any(pattern in filename_lower for pattern in demo_patterns):
            return True
        
        # Skip scripts/tools outside of src/ (unless they're part of the feature)
        if filename.startswith('scripts/') or filename.startswith('tools/') or filename.startswith('bin/'):
            # Only review if they're in src/ or feature directories
            if not any(dir in filename for dir in ['src/', 'lib/', 'app/', 'features/']):
                return True
        
        # Skip config files outside of src/ or feature directories
        config_extensions = ['.json', '.yaml', '.yml']
        if any(filename.endswith(ext) for ext in config_extensions):
            # Only review if in src/, lib/, app/, or feature directories
            if not any(dir in filename for dir in ['src/', 'lib/', 'app/', 'features/']):
                return True
        
        return False
    
    def _is_file_related_to_jira_ticket(self, filename: str) -> bool:
        """
        Check if a file is related to the current JIRA ticket based on ticket summary/description
        This is a fallback when commit-based filtering doesn't work
        """
        if not self.jira_issue:
            return True  # If no JIRA ticket, review all files
        
        jira_summary = self.jira_issue.get('summary', '').lower()
        jira_description = self.jira_issue.get('description', '').lower()
        filename_lower = filename.lower()
        
        # Extract keywords from JIRA ticket
        keywords = []
        if 'payment' in jira_summary or 'payment' in jira_description:
            keywords.extend(['payment', 'pay', 'transaction', 'refund', 'billing'])
        if 'login' in jira_summary or 'authentication' in jira_summary or 'auth' in jira_summary:
            keywords.extend(['login', 'auth', 'authentication', 'session', 'token'])
        if 'profile' in jira_summary or 'user profile' in jira_summary:
            keywords.extend(['profile', 'user'])
        
        # Check if filename contains any relevant keywords
        if keywords:
            if any(keyword in filename_lower for keyword in keywords):
                return True
            # If no keywords match, it's probably not related
            return False
        
        # If we can't determine, be conservative and review it
        return True
    
    def _filter_out_of_scope_files(self, out_of_scope_files: set) -> set:
        """
        Filter out files that are actually in scope based on JIRA ticket context.
        This prevents false positives where authentication-related files are flagged as out-of-scope.
        """
        if not self.jira_issue:
            return out_of_scope_files
        
        jira_summary = self.jira_issue.get('summary', '').lower()
        jira_description = self.jira_issue.get('description', '').lower()
        
        # Check if ticket is about authentication/login
        auth_keywords = ['login', 'authentication', 'auth', 'session', 'token', 'password', 'user login']
        is_auth_ticket = any(keyword in jira_summary or keyword in jira_description for keyword in auth_keywords)
        
        if not is_auth_ticket:
            return out_of_scope_files
        
        # Files that are clearly in scope for authentication tickets
        in_scope_patterns = [
            'login', 'auth', 'authentication', 'session', 'token', 'password',
            'middleware', 'service', 'controller', 'route', 'model'
        ]
        
        # Files that are clearly out of scope (CI/CD, docs, demos)
        always_out_of_scope = [
            '.github/', '.gitlab/', 'bitbucket-pipelines',
            'demo_', 'example_', 'test_', '_test.', '.test.',
            'README', 'CHANGELOG', 'LICENSE', '.md',
            'package.json', 'requirements.txt', 'Dockerfile',
            'docker-compose', '.config', '.yml', '.yaml'
        ]
        
        filtered = set()
        for file in out_of_scope_files:
            file_lower = file.lower()
            
            # Always include files that are clearly out of scope
            if any(pattern in file_lower for pattern in always_out_of_scope):
                filtered.add(file)
            # Exclude files that match in-scope patterns for auth tickets
            elif any(pattern in file_lower for pattern in in_scope_patterns):
                # This file is likely in scope, don't include it
                continue
            else:
                # Keep other files as potentially out of scope
                filtered.add(file)
        
        return filtered
    
    def _extract_code_snippet(self, file_content: str, line_number: Optional[int], context: int = 2) -> Optional[str]:
        """Return code snippet with line numbers around the specified line."""
        if not isinstance(line_number, int):
            return None
        lines = file_content.splitlines()
        if line_number < 1 or line_number > len(lines):
            return None

        start = max(line_number - 1 - context, 0)
        end = min(line_number + context, len(lines))
        snippet_lines = []
        for idx in range(start, end):
            pointer = ">" if (idx + 1) == line_number else " "
            snippet_lines.append(f"{idx + 1:04d}{pointer} {lines[idx].rstrip()}")
        return "\n".join(snippet_lines)

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
    
    def _build_enhanced_prompt(self, file_diff: FileDiff, file_content: str) -> str:
        """Build AI prompt with SRS and JIRA context if available"""
        jira_context = self._build_jira_context()
        srs_context = self.srs_context or ""
        
        # Get list of all changed files for scope check
        changed_files = [fd.filename for fd in getattr(self, '_all_file_diffs', [])]
        
        # Calculate total PR size across all files
        total_additions = sum(fd.additions for fd in getattr(self, '_all_file_diffs', []))
        total_deletions = sum(fd.deletions for fd in getattr(self, '_all_file_diffs', []))
        total_changes = total_additions + total_deletions
        
        # PR size warning
        pr_size_warning = ""
        if len(changed_files) > 10 or total_changes > 500:
            pr_size_warning = "\n⚠️ **PR SIZE WARNING**: This PR is large. Consider breaking it into smaller, focused PRs for easier review."
        
        # Build base prompt
        prompt = f"""You are a senior code reviewer with 10+ years of experience. Review the following code changes with the rigor and standards expected from a team lead or principal engineer. Provide constructive, specific, and actionable feedback.

{srs_context if srs_context else ""}
{jira_context if jira_context else ""}

## CODE CHANGES

**File:** {file_diff.filename}
**Status:** {file_diff.status}
**Changes:** +{file_diff.additions} -{file_diff.deletions}

**All Changed Files in PR:** ({len(changed_files)} files)
{chr(10).join(f"- {f}" for f in changed_files)}

**PR Size Analysis:**
- Total files changed: {len(changed_files)}
- Total lines added: {total_additions}
- Total lines deleted: {total_deletions}
- Total changes: {total_changes} lines{pr_size_warning}

**DIFF:**
{file_diff.patch}

**FULL FILE CONTENT:**
{file_content[:8000]}  # Limited to 8k chars for faster processing

## REVIEW REQUIREMENTS

"""
        
        # Add SRS-specific requirements if SRS is available
        if srs_context:
            prompt += """
**CRITICAL: Code must align with SRS requirements**

1. **SRS Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches SRS specifications
   - ✅ Check all functional requirements from SRS are met
   - ✅ Verify non-functional requirements (performance, security, scalability) are addressed
   - ❌ Flag any deviations from SRS requirements
   - ❌ Flag missing implementations required by SRS
   - ⚠️  Highlight any assumptions or interpretations that differ from SRS

2. **Architecture Alignment**:
   - Verify code follows architectural patterns specified in SRS
   - Check system design aligns with SRS architecture diagrams/descriptions
   - Flag any architectural violations

3. **Domain Knowledge**:
   - Use SRS context to understand business rules and domain logic
   - Verify business logic implementation matches SRS requirements
   - Flag incorrect business rule implementations

"""
        
        # Add JIRA-specific requirements if JIRA ticket is available
        if self.jira_issue:
            subtasks = self.jira_issue.get('subtasks', [])
            has_subtasks = len(subtasks) > 0
            
            prompt += f"""
**CRITICAL: This code must be evaluated against JIRA ticket {self.jira_key}**

1. **Requirement Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches JIRA description
   - ✅ Check all acceptance criteria are met
   - ❌ Flag any missing acceptance criteria
   - ❌ Flag any out-of-scope changes
   - ⚠️  Highlight files changed that are unrelated to JIRA scope

2. **Scope Validation**:
   - Review if ALL changed files are relevant to JIRA ticket {self.jira_key}
   - **IMPORTANT**: Files related to the ticket topic ARE IN SCOPE. For example:
     * For login/authentication tickets: controllers, services, middleware, routes, models, utils related to auth ARE IN SCOPE
     * Files with names containing: login, auth, authentication, session, token, password, user (when related to auth) ARE IN SCOPE
     * Only flag files as out-of-scope if they are clearly unrelated (e.g., documentation updates, CI/CD configs, demo files, unrelated features)
   - Flag any files that seem completely unrelated to the ticket requirements
   - Ensure no accidental changes to unrelated functionality
   - **DO NOT flag authentication-related files (controllers, services, middleware) as out-of-scope for authentication tickets**

3. **Acceptance Criteria Checklist**:
   - Create a checklist showing which acceptance criteria are met
   - Clearly mark any missing or incomplete criteria
   - Provide specific line references where criteria are implemented
   - Treat description as the primary source of acceptance criteria

"""
            
            # Add subtask coverage if subtasks exist
            if has_subtasks:
                prompt += f"""4. **Subtask Coverage** (🧾):
   - Verify implementation covers ALL subtasks:
"""
                for subtask in subtasks:
                    subtask_key = subtask.get('key', '')
                    subtask_summary = subtask.get('summary', '')
                    prompt += f"     - **{subtask_key}**: {subtask_summary}\n"
                prompt += """   - Check if each subtask requirement is addressed in the code
   - Flag any subtasks that are not implemented
   - Provide evidence of subtask implementation (file/line references)

"""
                prompt += """5. **Testing Requirements**:
"""
            else:
                prompt += """4. **Testing Requirements**:
"""
            
            prompt += """   - If business logic changed and no tests were added: ⚠️ WARN explicitly
   - Verify test coverage for new functionality
   - Check if acceptance criteria are testable
   - Apply stricter validation if JIRA summary or subtasks imply backend-critical changes

6. **Quality Enforcement**:
   - Warn if files changed are not aligned with JIRA scope
   - Flag business logic changes without corresponding tests
   - Apply stricter checks for critical backend changes
"""
        else:
            prompt += """
Please provide a detailed code review focusing on:
"""
        
        # Standard review categories
        prompt += """
6. **Code Quality**: Best practices, clean code principles, maintainability
7. **Potential Bugs**: Logic errors, edge cases, null pointer issues
8. **Security**: Vulnerabilities, injection risks, authentication/authorization issues
   - **CRITICAL**: Check for insecure defaults (e.g., public endpoints without authentication)
   - Flag crypto misuse: weak hashing algorithms (MD5, SHA1), incorrect encryption usage
   - Verify proper use of cryptographic libraries and algorithms
   - Check for command injection patterns (exec, eval, system calls with user input)
   - Flag XSS vulnerabilities in dynamic content rendering
   - Verify proper input encoding/escaping
9. **Performance & Scalability**:
   - **CRITICAL**: Flag unbounded loops or recursion risks (missing termination conditions)
   - Check for inefficient data structures (using array when Set/Map needed, etc.)
   - Flag repeated expensive calls (DB, API, filesystem) that could be cached
   - Identify missing caching opportunities for frequently accessed data
   - Flag large object creation inside loops (should be created outside)
   - Check for memory-intensive operations in loops
   - Verify proper use of pagination for large datasets
10. **Code Duplication & Reusability**:
   - **CRITICAL**: Flag duplicated code that should be extracted into reusable components/services
   - React: Flag duplicated components, hooks, or utility functions that should be shared
   - Backend: Flag duplicated API logic across controllers/services (extract to shared services)
   - Flag repeated database query patterns (extract to query helpers/utilities)
   - Suggest creating shared components/services/utilities for repeated code
   - Check for opportunities to use design patterns (Factory, Strategy, etc.) to reduce duplication
11. **Design Patterns**: Suggest better architectural patterns if applicable
12. **Testing**: Missing test cases or testability issues

**FRONTEND & BACKEND BEST PRACTICES (SME CHECKLIST):**

29. **Unused Code & Imports**:
   - **CRITICAL**: Flag unused variables, imports, and dead code
   - React: Flag unused useState, useEffect, props, and imports
   - Flag unnecessary state when values can be computed/derived
   - Clean up unused dependencies in effect hooks
   - Backend: Flag unused variables, imports, and unused ORM models/relationships
   - Remove unused functions, classes, and modules
   - Flag unused parameters in function signatures

30. **Commented-Out Code**:
   - **CRITICAL**: Never commit commented-out code
   - Flag commented JSX, API logic, SQL queries, or any commented code blocks
   - Suggest using Git history or feature flags instead of commented code
   - Remove commented debugging code, TODO comments with old code, or experimental code

31. **Hard-Coded Values & Configuration**:
   - **CRITICAL**: Move all hard-coded values to config/environment files
   - Flag hard-coded API URLs, endpoints, or service URLs (should be in config)
   - Flag hard-coded constants, magic numbers, or feature flags (should be configurable)
   - Flag hard-coded environment-specific values (dev/staging/prod URLs)
   - Enforce use of environment variables (.env files) or configuration modules
   - Never allow hard-coded secrets, tokens, or database credentials (covered in secrets check)

32. **Method/Function Signature Quality**:
   - React: Verify components have clear, well-named props
   - Flag components with excessive props (suggest using objects/context)
   - Backend: Verify API endpoints have explicit request/response schemas
   - Flag missing request payload validation (should use DTOs/Pydantic models)
   - Ensure return types are predictable and consistent
   - Flag functions with unclear parameter names or too many parameters
   - Verify function signatures are self-documenting

33. **Semantic Logic & Business Rules**:
   - **CRITICAL**: Ensure UI logic reflects backend business rules
   - Flag business logic embedded directly in React components (should be in backend/services)
   - Verify validation and business rules are centralized in backend services
   - Check conditional logic is readable and intention-revealing
   - Flag complex business logic in frontend that should be server-side
   - Ensure business rules are consistent between frontend and backend

34. **Performance - Loops, Rendering, and Database**:
   - **CRITICAL**: Optimize loops, rendering, and database calls
   - React Performance:
     * Flag unnecessary re-renders (check dependency arrays in useEffect/useMemo/useCallback)
     * Flag missing memoization where expensive computations occur
     * Flag loops inside render that perform heavy logic
     * Verify useMemo/useCallback are used appropriately (not overused)
   - Database Performance:
     * **CRITICAL**: Flag database queries inside for loops (use bulk operations instead)
     * Prefer bulk inserts, joins, IN queries, and set-based operations
     * Flag N+1 query problems (use eager loading or batch queries)
     * Verify indexes exist for frequently filtered columns
     * Flag sequential await calls in loops when parallel execution is safe
     * Check for missing database query optimization

35. **Promises & Async Handling**:
   - **CRITICAL**: Proper async/await and promise handling
   - Node.js:
     * Flag wrapping synchronous logic inside new Promise() (unnecessary)
     * Use async/await consistently (avoid mixing with .then())
     * Flag sequential await calls in loops when parallel execution is safe (use Promise.all)
     * Always handle Promise rejections (missing .catch() or try/catch)
     * Flag unhandled promise rejections
   - FastAPI/Python:
     * Use async endpoints only when I/O-bound operations exist
     * Flag blocking calls inside async routes
     * Ensure DB sessions are properly closed or scoped
     * Verify proper async context management

36. **Code Formatting & Indentation**:
   - React: Maintain consistent JSX indentation and component structure
   - Flag deeply nested JSX (suggest breaking into smaller components)
   - Backend: Follow language-specific formatting standards
   - Ensure consistent indentation for conditionals, loops, and transactions
   - Flag inconsistent spacing, bracket placement, or indentation

37. **Security - Frontend & Backend**:
   - Frontend Security:
     * **CRITICAL**: Never trust client-side validation alone (always validate server-side)
     * Flag sensitive values exposed in browser logs, console.log, or source code
     * Verify proper input sanitization before rendering
     * Check for XSS vulnerabilities in dynamic content rendering
   - Backend Security (enhanced):
     * Validate and sanitize all user inputs (covered, but emphasize)
     * Prevent SQL injection using ORM query bindings (covered)
     * Enforce authentication and authorization on every protected route (covered)
     * Ensure proper CORS configuration
     * Do not leak internal errors or stack traces (covered in error_leakage)

38. **Logging, Error Handling & Testing**:
   - Use structured and meaningful logs (covered in logging standards)
   - Avoid logging sensitive data (covered in PII check)
   - Ensure graceful error handling with clear API responses (covered)
   - **CRITICAL**: Validate unit tests exist for:
     * Services and business logic
     * API endpoints
     * Critical UI flows/components
   - Add integration tests for complex database interactions
   - Flag missing test coverage for new functionality

## ADDITIONAL SENIOR REVIEWER STANDARDS

**HIGH PRIORITY CHECKS:**

13. **Code Style & Consistency**:
   - Check code formatting consistency (indentation, spacing, brackets)
   - Validate naming conventions (camelCase, PascalCase, snake_case, kebab-case) match project standards
   - Verify file organization and structure follows project conventions
   - Check import/require ordering and grouping
   - Flag inconsistent coding styles across files
   - Ensure code follows language-specific style guides (ESLint, Prettier, PEP 8, etc.)

14. **Documentation Requirements**:
   - Verify functions/classes have proper documentation (JSDoc, docstrings, JavaDoc)
   - Check for inline comments explaining complex logic or business rules
   - Flag missing documentation for public APIs, classes, and complex functions
   - Ensure README/documentation is updated for new features
   - Check that code examples in documentation are accurate
   - Verify parameter and return type documentation

15. **Error Handling & Resilience**:
   - **CRITICAL**: Flag swallowed exceptions (empty catch blocks that ignore errors)
   - Flag overly generic exception handling (catch (Exception) or catch (Error) without specific handling)
   - Check for inconsistent error propagation (some errors logged, others not)
   - Verify correct HTTP status codes for API responses (200 for success, 400 for client errors, 500 for server errors)
   - Flag missing fallback logic for critical operations
   - Ensure errors are caught and handled appropriately (try-catch, promises, async/await)
   - Check for unhandled promise rejections
   - Verify graceful degradation when errors occur
   - Flag generic catch blocks that swallow errors without logging
   - Validate error messages are user-friendly and informative (not exposing internals)

16. **Observability & Operability**:
   - **CRITICAL**: Check for missing or noisy logging (too many logs or no logs at all)
   - Verify appropriate log levels are used (DEBUG, INFO, WARN, ERROR)
   - Flag missing correlation IDs / trace IDs for request tracking
   - Check for missing metrics for critical paths (success/failure rates, latency)
   - Flag missing health checks for new components/services
   - Verify feature flags are used for risky changes (not hard-coded)
   - Verify structured logging format (JSON, key-value pairs)
   - Ensure sensitive data (passwords, tokens, PII) is NOT logged
   - Check log messages are meaningful and include context
   - Verify performance-critical operations are logged
   - Flag console.log statements in production code (should use proper logger)
   - Check logging doesn't create performance bottlenecks

17. **Architecture Alignment**:
   - Verify code follows existing architectural patterns in the codebase
   - Check separation of concerns (business logic, data access, presentation)
   - Validate dependency direction (high-level modules shouldn't depend on low-level)
   - Ensure code fits the overall system architecture
   - Check for architectural violations (circular dependencies, tight coupling)
   - Verify adherence to SOLID principles
   - Flag code that doesn't align with existing patterns

**MEDIUM PRIORITY CHECKS:**

18. **API Design & Contract Consistency**:
   - **CRITICAL**: Flag breaking API changes without versioning
   - Check for backward compatibility issues (removed fields, changed types, etc.)
   - Verify consistent request/response shapes across similar endpoints
   - Flag missing validation annotations (required fields, data types, constraints)
   - Check for DTO vs domain leakage (domain objects exposed directly in API responses)
   - Flag incorrect default values in API responses or request handling
   - Validate RESTful API conventions (HTTP methods, status codes, URLs)
   - Check API versioning strategy is followed
   - Verify request/response validation
   - Ensure consistent API response format (success/error structure)
   - Check API documentation is complete and accurate
   - Verify proper HTTP status codes are used (200, 201, 400, 401, 404, 500, etc.)
   - Flag missing input validation on API endpoints
   - Check rate limiting is properly implemented
   - Verify API endpoints follow naming conventions

19. **Database Query Optimization**:
   - Check for N+1 query problems
   - Verify proper use of database indexes
   - Flag inefficient queries (full table scans, missing WHERE clauses)
   - Check for SQL injection vulnerabilities (parameterized queries)
   - Verify transaction management is correct
   - Check connection pooling is used appropriately
   - Flag queries that fetch unnecessary data (SELECT *)
   - Verify database queries are optimized (EXPLAIN plans)
   - Check for missing indexes on frequently queried columns

20. **Concurrency & Thread Safety**:
   - **CRITICAL**: Check for race conditions in multi-threaded code
   - Verify thread safety (locks, mutexes, atomic operations)
   - Check for deadlock potential
   - Flag shared mutable state without proper synchronization
   - Flag non-thread-safe collections used in concurrent contexts (e.g., ArrayList in Java, regular dict in Python)
   - Check for proper handling of concurrent requests
   - Validate async/await patterns are used correctly
   - Verify promise/async error handling
   - Check for memory leaks in async operations
   - Flag improper use of async/await that could cause race conditions

21. **Memory & Resource Management**:
   - Check for memory leaks (unclosed connections, event listeners, timers)
   - Verify resource cleanup (file handles, database connections, streams)
   - Check for proper disposal of resources (using statements, finally blocks)
   - Flag unbounded data structures that could cause memory issues
   - Verify large objects are properly released
   - Check for circular references that prevent garbage collection
   - Verify streaming/chunking for large data processing

22. **PR Quality Checks**:
   - Check PR size (flag if too large - suggest breaking into smaller PRs)
   - Verify PR description is clear and includes:
     * What changes were made
     * Why the changes were made
     * How to test the changes
     * Screenshots/demos if UI changes
   - Check commit messages follow conventions (conventional commits)
   - Verify branch naming follows standards
   - Flag PRs that mix unrelated changes
   - Check if PR addresses a single concern/feature
   - Verify breaking changes are documented

**CRITICAL SECURITY & COMPLIANCE CHECKS (SME FEEDBACK):**

23. **Authorization - Object-Level Access Control**:
   - **CRITICAL**: When endpoints access user/customer/tenant data, verify object-level authorization is enforced
   - Flag endpoints that query user data without proper authorization checks (e.g., missing WHERE user_id = ? or tenant_id = ?)
   - Check for authorization middleware/checks before data access operations
   - Verify that users can only access their own records (not other users' data)
   - Flag missing authorization checks in:
     * GET endpoints that return user-specific data
     * UPDATE/DELETE operations on user records
     * Any query that filters by user_id, customer_id, tenant_id without validation
   - Ensure authorization happens server-side, not just client-side
   - Check for proper role-based access control (RBAC) when applicable

24. **External Integrations - Safe Failure Handling**:
   - **CRITICAL**: All third-party/internal service calls must have proper error handling
   - Flag external API calls (fetch, axios, http requests) without try/catch blocks
   - Require meaningful fallback/error responses for external service failures
   - Check for graceful degradation when external services fail
   - Flag missing timeout handling for external calls
   - Verify circuit breaker patterns for critical external dependencies
   - Check for proper retry logic with exponential backoff
   - Ensure one dependency failure doesn't break the entire flow
   - Flag missing error handling for:
     * Payment gateway calls
     * Email/SMS service calls
     * Third-party API integrations
     * Internal microservice calls

25. **Database Correctness & Constraints**:
   - **CRITICAL**: Flag missing database constraints and optimizations
   - Check for missing indexes on frequently queried columns (especially in WHERE clauses)
   - Flag UPDATE/DELETE queries without WHERE clauses (prevents accidental mass updates)
   - Verify transaction boundaries for multi-step database operations
   - Check for missing foreign key constraints (if schema context available)
   - Flag queries that could cause data integrity issues
   - Verify proper use of database transactions for atomic operations
   - Check for missing unique constraints on columns that should be unique
   - Flag N+1 query problems
   - Verify proper connection pooling usage
   - **Note**: Full schema validation requires DB schema/migrations in scope (to be enhanced)

26. **Secrets & Configuration Safety**:
   - **CRITICAL**: Never allow hardcoded secrets, tokens, or sensitive configuration
   - Detect and flag hardcoded:
     * API keys (pattern: api[_-]?key, apikey, secret[_-]?key)
     * Passwords (password\s*=\s*['\"][^'\"]+)
     * Tokens (token\s*=\s*['\"][^'\"]+, jwt[_-]?secret)
     * AWS keys (aws[_-]?(access[_-]?key|secret[_-]?key))
     * Database credentials (db[_-]?(password|pass|pwd))
     * OAuth secrets (client[_-]?secret, oauth[_-]?secret)
     * Connection strings with credentials
   - Flag environment-specific URLs hardcoded in code:
     * localhost, 127.0.0.1, staging URLs, production URLs
   - **CRITICAL**: Flag environment-specific behavior hardcoded (should use config/env)
   - Check for missing configuration defaults (required configs should have defaults)
   - Flag unsafe feature toggles (feature flags that could cause security issues)
   - Verify config values are validated (type, range, required fields)
   - Flag secrets in config files (should be in environment variables or secret management)
   - Enforce configuration via environment variables or config layer
   - Flag feature flags hardcoded in code (should be in config)
   - Check for secrets in:
     * Variable assignments
     * String literals
     * Configuration objects
     * Comments (sometimes developers leave secrets in comments)
   - Verify sensitive configs are not committed in PR

27. **Sensitive Data & PII Exposure**:
   - **CRITICAL**: Prevent PII and sensitive data exposure in APIs and logs
   - Flag unnecessary PII in API responses:
     * Email addresses (unless required)
     * Phone numbers (unless required)
     * PAN numbers (Indian tax ID pattern)
     * Aadhaar numbers (12-digit pattern)
     * Full addresses (unless required)
     * Date of birth
     * Social Security Numbers (SSN patterns)
   - Detect and flag sensitive data in logs:
     * Passwords (password, pwd, passwd in log messages)
     * Tokens (token, jwt, access_token, refresh_token)
     * OTP codes (otp, verification[_-]?code)
     * Credit card numbers (pattern detection)
     * PAN/Aadhaar numbers
     * API keys or secrets
   - Flag storing secrets in plain text anywhere (database, files, variables)
   - Check for sensitive fields in:
     * API response objects
     * Log statements (console.log, logger.info with sensitive data)
     * Error messages (shouldn't expose internal details)
     * Debug output
   - Verify data masking/redaction for sensitive fields in logs
   - Flag unnecessary sensitive fields returned in GET responses

28. **Error Handling - No Internal Leakage**:
   - **CRITICAL**: Ensure error responses don't leak internal system details
   - Flag raw exception messages sent to clients (error.message, error.stack)
   - Check for stack traces in API responses
   - Verify detailed error objects are not exposed to end users
   - Flag database error messages exposed to clients (should be sanitized)
   - Ensure error responses are user-friendly and don't reveal:
     * Stack traces
     * File paths
     * Database connection strings
     * Internal system architecture
     * Code structure or variable names
   - Verify error logging happens server-side (detailed errors in logs, not responses)
   - Check for proper error sanitization before sending to client

## OUTPUT FORMAT

Format your response as JSON with the following structure:
{{
  "overall_assessment": "Brief summary of the changes and compliance with JIRA requirements",
  "severity": "info|warning|critical",
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
      "line": <line_number or null>,
      "severity": "info|warning|error",
      "category": "requirement|quality|bug|security|performance|boilerplate|design|testing|scope|style|documentation|error_handling|logging|architecture|api|database|concurrency|memory|pr_quality|authorization|external_integration|db_constraints|secrets|pii|error_leakage|duplication|unused_code|commented_code|hardcoded_values|signature|business_logic|async_handling|formatting|frontend_security|test_coverage|insecure_defaults|crypto|input_validation|unbounded_loops|inefficient_data_structures|caching|swallowed_exceptions|error_propagation|thread_safety|api_contract|observability|config_safety",
      "title": "Brief issue title",
      "description": "Detailed explanation",
      "suggestion": "Specific recommendation or code example"
    }}
  ],
  "positive_aspects": ["List of good practices found in the code"]
}}

**IMPORTANT:**
- If acceptance criteria are missing or violated, mark severity as "error" and set final_verdict to "Changes Requested"
- **SCOPE DETECTION RULES**: 
  * For authentication/login tickets: Files in paths like `src/controllers/*login*`, `src/services/*auth*`, `src/middleware/*auth*`, `src/routes/*auth*` ARE IN SCOPE
  * Only flag files as out-of-scope if they are clearly unrelated (CI/CD configs, documentation, demo files, unrelated features)
  * DO NOT flag authentication-related code files as out-of-scope for authentication tickets
- If files are out of scope, create issues with category "scope"
- If subtasks are not covered, mark them as "❌ Missing" in subtask_coverage
- Be specific about which acceptance criteria are met/missing
- Provide line references for requirement implementation
- If business logic changed without tests, create a "testing" issue with severity "warning"
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

Be constructive, specific, and helpful. Focus on meaningful improvements."""
        
        return prompt
    
    def review_file(self, file_diff: FileDiff) -> Optional[Dict]:
        """Review a single file using AI"""
        print(f"📝 Reviewing {file_diff.filename}...")
        
        # Read the full file content if it exists (limit to 8000 chars for faster processing)
        try:
            with open(file_diff.filename, 'r', encoding='utf-8') as f:
                full_content = f.read()
                # Limit file content to 8000 chars to reduce prompt size and API latency
                file_content = full_content[:8000] + ("\n... (truncated)" if len(full_content) > 8000 else "")
        except:
            file_content = "File not accessible or was deleted"
        
        # Build enhanced prompt with JIRA context
        prompt = self._build_enhanced_prompt(file_diff, file_content)

        try:
            # Enhanced system message for JIRA-aware reviews
            system_message = """You are a senior code reviewer with 10+ years of experience, acting as a team lead or principal engineer. You have deep expertise in:
- Software engineering best practices and clean code principles
- Security vulnerabilities and OWASP Top 10
- Design patterns and architecture
- Code style, documentation, and maintainability standards
- Error handling, logging, and observability
- API design, database optimization, and performance
- Concurrency, memory management, and resource handling
- Testing strategies and quality assurance

You review code with the same rigor and standards expected from a senior engineer or team lead. Your reviews are:
- Constructive and educational (help developers learn)
- Specific and actionable (provide clear guidance)
- Balanced (acknowledge good practices, suggest improvements)
- Professional and respectful (maintain positive team culture)"""
            
            if self.jira_issue:
                system_message += "\n\nYou are also an expert at evaluating code implementations against JIRA ticket requirements and acceptance criteria. You must strictly verify that code changes align with the specified requirements."
            
            # Use faster model settings for better performance
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for faster responses
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for faster, more consistent responses
                response_format={"type": "json_object"},
                max_tokens=4000  # Limit response size for faster processing
            )
            
            review_result = json.loads(response.choices[0].message.content)
            for issue in review_result.get('issues', []):
                line_number = issue.get('line')
                snippet = self._extract_code_snippet(file_content, line_number)
                issue['code_snippet'] = snippet
                issue['line_valid'] = snippet is not None
            return review_result
            
        except Exception as e:
            print(f"❌ Error reviewing {file_diff.filename}: {str(e)}")
            return None
    
    def _build_line_map(self, patch: str) -> Dict[int, int]:
        """Map actual file line numbers to diff positions for inline comments."""
        line_map: Dict[int, int] = {}
        current_line = 0
        diff_line = 0

        for raw_line in patch.splitlines():
            if raw_line.startswith('@@'):
                match = re.search(r'\+(\d+)', raw_line)
                if match:
                    current_line = int(match.group(1))
                    diff_line = 0
                continue
            if raw_line.startswith('+++') or raw_line.startswith('---'):
                continue

            diff_line += 1

            if raw_line.startswith('+'):
                line_map[current_line] = diff_line
                current_line += 1
            elif raw_line.startswith('-'):
                continue
            else:
                line_map[current_line] = diff_line
                current_line += 1

        return line_map

    def _delete_previous_ai_comments(self):
        """Delete previous AI review comments to prevent email spam"""
        try:
            # Get all PR comments
            comments_url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.pr_number}/comments"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(comments_url, headers=headers)
            if response.status_code == 200:
                comments = response.json()
                deleted_count = 0
                for comment in comments:
                    # Check if it's an AI-generated comment
                    if '🤖 Generated by AI Code Reviewer' in comment.get('body', ''):
                        delete_url = f"https://api.github.com/repos/{self.repo_name}/pulls/comments/{comment['id']}"
                        delete_response = requests.delete(delete_url, headers=headers)
                        if delete_response.status_code == 204:
                            deleted_count += 1
                
                if deleted_count > 0:
                    print(f"🗑️  Deleted {deleted_count} previous AI comments")
        except Exception as e:
            print(f"⚠️  Could not delete previous comments: {str(e)}")
    
    def _delete_previous_summary_comment(self):
        """Delete previous summary comment"""
        try:
            # Get all issue comments (summary is posted as issue comment)
            comments_url = f"https://api.github.com/repos/{self.repo_name}/issues/{self.pr_number}/comments"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(comments_url, headers=headers)
            if response.status_code == 200:
                comments = response.json()
                for comment in comments:
                    # Check if it's an AI summary comment
                    if '🤖 AI Code Review Summary' in comment.get('body', ''):
                        delete_url = f"https://api.github.com/repos/{self.repo_name}/issues/comments/{comment['id']}"
                        delete_response = requests.delete(delete_url, headers=headers)
                        if delete_response.status_code == 204:
                            print("🗑️  Deleted previous summary comment")
                            break
        except Exception as e:
            print(f"⚠️  Could not delete previous summary: {str(e)}")
    
    def post_review_comments(self, file_diff: FileDiff, review: Dict):
        """Post review comments to GitHub PR"""
        if not review or not review.get('issues'):
            return
        
        github_api_url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.pr_number}/comments"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        line_map = self._build_line_map(file_diff.patch)

        for issue in review['issues']:
            # Create comment body
            emoji_map = {
                'quality': '🎨',
                'bug': '🐛',
                'security': '🔒',
                'performance': '⚡',
                'boilerplate': '♻️',
                'design': '🏗️',
                'testing': '🧪'
            }
            
            severity_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '🔴'
            }
            
            emoji = emoji_map.get(issue.get('category', ''), '💡')
            severity = severity_emoji.get(issue.get('severity', 'info'), 'ℹ️')
            
            comment_body = f"""{emoji} **{issue['title']}** {severity}

**Category**: {issue.get('category', 'general')}

{issue['description']}

**Suggestion**:
{issue.get('suggestion', 'No specific suggestion provided')}

---
*🤖 Generated by AI Code Reviewer*
"""
            snippet = issue.get('code_snippet')
            if snippet:
                comment_body += f"\n**Code context:**\n```\n{snippet}\n```\n"
            
            # Try to find the specific line in the diff
            line_number = issue.get('line')
            line_valid = issue.get('line_valid', False)
            mapped_line = line_map.get(line_number) if isinstance(line_number, int) else None

            if line_number and line_valid:
                # Post as inline comment
                comment_data = {
                    'body': comment_body,
                    'commit_id': self.head_sha,
                    'path': file_diff.filename,
                    'line': line_number,
                    'side': 'RIGHT'
                }
                
                try:
                    response = requests.post(github_api_url, headers=headers, json=comment_data)
                    if response.status_code == 201:
                        print(f"✅ Posted comment on {file_diff.filename}:{line_number}")
                    else:
                        print(f"⚠️  Failed to post inline comment: {response.status_code}")
                        # Fall back to storing for summary
                        self.review_comments.append(ReviewComment(
                            file=file_diff.filename,
                            line=line_number or 0,
                            comment=comment_body,
                            severity=issue.get('severity', 'info')
                        ))
                except Exception as e:
                    print(f"⚠️  Error posting comment: {str(e)}")
            else:
                note = "Line could not be matched precisely; including in summary instead."
                comment_body += f"\n_{note}_\n"
                self.review_comments.append(ReviewComment(
                    file=file_diff.filename,
                    line=line_number or 0,
                    comment=comment_body,
                    severity=issue.get('severity', 'info')
                ))
    
    def _should_request_changes(self, file_reviews: List[tuple]) -> bool:
        """Determine if PR should be marked as 'Changes Requested' based on AI final verdict"""
        if not self.jira_issue:
            return False
        
        # Check AI's final verdict first (most reliable)
        for _, review in file_reviews:
            if not review:
                continue
            
            jira_compliance = review.get('jira_compliance', {})
            final_verdict = jira_compliance.get('final_verdict', '').lower()
            
            # If AI explicitly says "Changes Requested", honor it
            if 'changes requested' in final_verdict or 'request changes' in final_verdict:
                return True
            
            # If AI says "Approve", check if there are still issues
            if 'approve' in final_verdict:
                # Still check for critical issues
                missing_criteria = jira_compliance.get('missing_criteria', [])
                out_of_scope = jira_compliance.get('out_of_scope_files', [])
                
                # Check subtask coverage
                subtask_coverage = jira_compliance.get('subtask_coverage', [])
                missing_subtasks = [st for st in subtask_coverage if 'missing' in st.get('status', '').lower()]
                
                if missing_criteria or out_of_scope or missing_subtasks:
                    return True
                
                # Check for critical requirement issues
                for issue in review.get('issues', []):
                    if issue.get('severity') == 'error' and issue.get('category') in ['requirement', 'scope']:
                        return True
            else:
                # No explicit verdict, check traditional indicators
                missing_criteria = jira_compliance.get('missing_criteria', [])
                out_of_scope = jira_compliance.get('out_of_scope_files', [])
                subtask_coverage = jira_compliance.get('subtask_coverage', [])
                missing_subtasks = [st for st in subtask_coverage if 'missing' in st.get('status', '').lower()]
                
                if missing_criteria or out_of_scope or missing_subtasks:
                    return True
                
                # Check for critical requirement issues
                for issue in review.get('issues', []):
                    if issue.get('severity') == 'error' and issue.get('category') in ['requirement', 'scope']:
                        return True
        
        return False
    
    def _submit_review(self, file_reviews: List[tuple]):
        """Submit PR review with appropriate state"""
        should_request_changes = self._should_request_changes(file_reviews)
        
        if not should_request_changes:
            return  # Don't submit review if no changes needed
        
        try:
            review_url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.pr_number}/reviews"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get all issues for review body
            all_issues = []
            out_of_scope_files = set()
            for file_diff, review in file_reviews:
                if review:
                    all_issues.extend(review.get('issues', []))
                    # Collect out-of-scope files from jira_compliance
                    jira_compliance = review.get('jira_compliance', {})
                    out_of_scope = jira_compliance.get('out_of_scope_files', [])
                    if out_of_scope:
                        out_of_scope_files.update(out_of_scope)
            
            # Filter critical issues (exclude duplicate out-of-scope messages)
            critical_issues = []
            seen_titles = set()
            for issue in all_issues:
                if issue.get('severity') == 'error' and issue.get('category') in ['requirement', 'scope']:
                    title = issue.get('title', '')
                    # Deduplicate: skip if we've seen this title before
                    if title not in seen_titles:
                        seen_titles.add(title)
                        critical_issues.append(issue)
            
            review_body = "## ⚠️ Changes Requested\n\n"
            review_body += "This PR does not fully meet the JIRA ticket requirements:\n\n"
            
            # Filter out-of-scope files to remove false positives
            filtered_out_of_scope = self._filter_out_of_scope_files(out_of_scope_files)
            
            # Add out-of-scope files section if any remain after filtering
            if filtered_out_of_scope:
                review_body += f"**Out-of-scope files detected:** {len(filtered_out_of_scope)} file(s) appear unrelated to the JIRA ticket.\n"
                review_body += "Please ensure all changes are relevant to the ticket requirements.\n\n"
            
            # Add other critical issues (limit to 3 to avoid repetition)
            other_issues = [i for i in critical_issues if 'out-of-scope' not in i.get('title', '').lower()][:3]
            for issue in other_issues:
                review_body += f"- **{issue.get('title')}**: {issue.get('description', '')[:200]}\n"
            
            review_data = {
                'body': review_body,
                'event': 'REQUEST_CHANGES',
                'comments': []  # Inline comments are posted separately
            }
            
            response = requests.post(review_url, headers=headers, json=review_data, timeout=10)
            
            if response.status_code == 200:
                print("📝 Submitted review: Changes Requested")
            else:
                print(f"⚠️  Could not submit review: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Exception submitting review: {str(e)}")
    
    def generate_review_summary(self, file_reviews: List[tuple]):
        """Generate a summary of the entire review"""
        print("📊 Generating review summary...")
        
        total_files = len(file_reviews)
        total_issues = sum(len(review.get('issues', [])) for _, review in file_reviews if review)
        
        critical_count = sum(
            1 for _, review in file_reviews if review 
            for issue in review.get('issues', []) 
            if issue.get('severity') == 'error'
        )
        warning_count = sum(
            1 for _, review in file_reviews if review 
            for issue in review.get('issues', []) 
            if issue.get('severity') == 'warning'
        )
        info_count = sum(
            1 for _, review in file_reviews if review 
            for issue in review.get('issues', []) 
            if issue.get('severity') == 'info'
        )
        
        summary = f"""# 🤖 AI Code Review Summary"""
        
        # Add SRS context if available
        if self.srs_context:
            summary += f"\n## 📚 SRS Context\n\n"
            summary += f"{self.srs_service.get_srs_summary()}\n\n"
        
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
- **Total Issues Found**: {total_issues}
  - 🔴 Critical: {critical_count}
  - ⚠️  Warnings: {warning_count}
  - ℹ️  Info: {info_count}

"""
        
        # Add JIRA compliance section if available
        if self.jira_issue:
            summary += "## 📋 JIRA Compliance Check\n\n"
            
            # Collect all compliance data across all files (deduplicate)
            all_compliant = True
            all_missing = set()
            all_out_of_scope = set()
            all_checklists = []
            all_subtask_coverage = []
            final_verdict = None
            
            for _, review in file_reviews:
                if not review:
                    continue
                
                jira_compliance = review.get('jira_compliance', {})
                matches = jira_compliance.get('matches_requirements', False)
                missing = jira_compliance.get('missing_criteria', [])
                out_of_scope = jira_compliance.get('out_of_scope_files', [])
                checklist = jira_compliance.get('acceptance_criteria_checklist', [])
                subtask_coverage = jira_compliance.get('subtask_coverage', [])
                verdict = jira_compliance.get('final_verdict', '')
                
                if not matches or missing or out_of_scope:
                    all_compliant = False
                
                # Collect unique missing criteria
                if missing:
                    all_missing.update(missing)
                
                # Collect unique out-of-scope files
                if out_of_scope:
                    all_out_of_scope.update(out_of_scope)
                
                # Collect checklists (use first non-empty one, or merge)
                if checklist and not all_checklists:
                    all_checklists = checklist
                
                # Collect subtask coverage (use first non-empty one, or merge)
                if subtask_coverage and not all_subtask_coverage:
                    all_subtask_coverage = subtask_coverage
                
                # Use first final verdict found
                if verdict and not final_verdict:
                    final_verdict = verdict
                
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
            if all_checklists:
                summary += "### 📋 Acceptance Criteria Checklist\n\n"
                for item in all_checklists:
                    summary += f"{item.get('status', '❓')} {item.get('criteria', 'N/A')}\n"
                    if item.get('evidence'):
                        summary += f"   *Evidence: {item.get('evidence')}*\n"
                summary += "\n"
            
            # Subtask Coverage
            if all_subtask_coverage:
                summary += "### 🧾 Subtask Coverage\n\n"
                for subtask in all_subtask_coverage:
                    subtask_key = subtask.get('subtask_key', 'N/A')
                    subtask_status = subtask.get('status', '❓')
                    subtask_evidence = subtask.get('evidence', '')
                    summary += f"{subtask_status} **{subtask_key}**\n"
                    if subtask_evidence:
                        summary += f"   *Evidence: {subtask_evidence}*\n"
                summary += "\n"
            
            # Missing Acceptance Criteria (deduplicated)
            if all_missing:
                summary += "### ❌ Missing Acceptance Criteria\n\n"
                for criteria in sorted(all_missing):
                    summary += f"- {criteria}\n"
                summary += "\n"
            
            # Out-of-Scope Files (deduplicated and filtered)
            if all_out_of_scope:
                # Filter out files that are clearly related to the JIRA ticket
                filtered_out_of_scope = self._filter_out_of_scope_files(all_out_of_scope)
                
                if filtered_out_of_scope:
                    summary += "### ⚠️ Out-of-Scope Files\n\n"
                    summary += f"The following {len(filtered_out_of_scope)} file(s) appear unrelated to JIRA ticket requirements:\n\n"
                    for file in sorted(filtered_out_of_scope):
                        summary += f"- `{file}`\n"
                    summary += "\n"
                else:
                    # If we filtered out all files, mention that authentication-related files are in scope
                    summary += "### ℹ️ Scope Note\n\n"
                    summary += "All changed files appear to be related to the JIRA ticket requirements.\n\n"
            
            if all_compliant:
                summary += "✅ **All JIRA requirements appear to be met!**\n\n"
            else:
                summary += "❌ **Some JIRA requirements are not met. Please review.**\n\n"
            
            summary += "---\n\n"
        
        summary += "\n---\n"
        summary += "*This review was automatically generated using AI. Please review the suggestions and use your judgment.*\n"
        summary += "\n**Note to Team Lead**: The AI has performed the initial review. Please focus on the critical and warning items, and verify the suggestions align with your project's standards.\n"
        
        # Save summary to file (in workspace root for workflow to find it)
        # Script runs from .github/scripts/, so go up 2 levels to workspace root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(os.path.dirname(script_dir))
        summary_path = os.path.join(workspace_root, 'review_summary.md')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"✅ Review summary saved to {summary_path}")
    
    def _get_pr_info(self):
        """Fetch PR title and branch name from GitHub API if not provided"""
        if self.pr_title and self.branch_name:
            return
        
        try:
            pr_url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.pr_number}"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(pr_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pr_data = response.json()
                self.pr_title = pr_data.get('title', '')
                self.branch_name = pr_data.get('head', {}).get('ref', '')
                print(f"📋 PR Title: {self.pr_title}")
                print(f"🌿 Branch: {self.branch_name}")
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
            self.branch_name, 
            self.pr_title, 
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
        """Post comment suggesting JIRA ticket link"""
        comment_body = """## ℹ️ JIRA Ticket (Optional)

This PR does not have a linked JIRA ticket. The review will proceed without JIRA context.

**To enable JIRA-aware reviews**, add a JIRA ticket key to:

- **PR Title** (e.g., `PROJ-123: Add login feature`)
- **Branch Name** (e.g., `feature/PROJ-123-login`)
- **Commit Message** (e.g., `PROJ-123: Implement login`)

**JIRA Key Format:** `[A-Z][A-Z0-9]+-[0-9]+` (e.g., `PROJ-123`, `ABC-456`)

Once a valid JIRA ticket is detected, the AI review will evaluate your code against the ticket's requirements and acceptance criteria.

---
*🤖 Generated by AI Code Reviewer*
"""
        
        try:
            comments_url = f"https://api.github.com/repos/{self.repo_name}/issues/{self.pr_number}/comments"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.post(comments_url, headers=headers, json={'body': comment_body}, timeout=10)
            
            if response.status_code == 201:
                print("📝 Posted comment requesting JIRA ticket")
            else:
                print(f"⚠️  Could not post JIRA request comment: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Exception posting JIRA request: {str(e)}")
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting AI Code Review...")
        print(f"📦 Repository: {self.repo_name}")
        print(f"🔀 PR #{self.pr_number}")
        print(f"📊 Comparing {self.base_sha[:7]} → {self.head_sha[:7]}")
        print("-" * 60)
        
        # Get PR info (title, branch)
        self._get_pr_info()
        
        # Load SRS documents for project context
        print("📚 Loading SRS documents for project context...")
        self.srs_context = self.srs_service.get_srs_context()
        if self.srs_context:
            print("✅ SRS context loaded successfully")
        else:
            print("ℹ️  No SRS documents found - proceeding without SRS context")
        
        # Detect and fetch JIRA ticket (optional)
        jira_available = False
        if self.jira_service.enabled:
            print("🔍 JIRA integration enabled - checking for JIRA ticket...")
            jira_available = self._detect_and_fetch_jira_ticket()
            
            if jira_available:
                print(f"✅ JIRA ticket {self.jira_key} found - will use JIRA context in review")
            else:
                print("ℹ️  No JIRA ticket found - proceeding without JIRA context")
        else:
            print("ℹ️  JIRA integration not configured - proceeding without JIRA context")
        
        # Determine review type
        if jira_available and self.srs_context:
            print("📋 Review Mode: JIRA-aware + SRS-aware (Full Context)")
        elif jira_available:
            print("📋 Review Mode: JIRA-aware (JIRA context only)")
        elif self.srs_context:
            print("📋 Review Mode: SRS-aware (SRS context only)")
        else:
            print("📋 Review Mode: Standard Code Review (No additional context)")
        
        # Always proceed with review regardless of JIRA/SRS availability
        
        # Delete previous AI comments to prevent email spam
        print("🧹 Cleaning up previous AI comments...")
        self._delete_previous_ai_comments()
        self._delete_previous_summary_comment()
        
        # Get PR diff
        file_diffs = self.get_pr_diff()
        
        if not file_diffs:
            print("ℹ️  No files to review")
            return
        
        print(f"📁 Found {len(file_diffs)} file(s) to review")
        print("-" * 60)
        
        # Review each file (with timing for performance monitoring)
        file_reviews = []
        # Store file_diffs for use in prompt building
        self._all_file_diffs = file_diffs
        
        import time
        start_time = time.time()
        
        for idx, file_diff in enumerate(file_diffs, 1):
            print(f"📝 [{idx}/{len(file_diffs)}] Reviewing {file_diff.filename}...")
            file_start = time.time()
            
            review = self.review_file(file_diff)
            
            file_elapsed = time.time() - file_start
            print(f"✅ [{idx}/{len(file_diffs)}] Completed {file_diff.filename} in {file_elapsed:.1f}s")
            
            if review:
                file_reviews.append((file_diff, review))
                self.post_review_comments(file_diff, review)
        
        total_elapsed = time.time() - start_time
        print(f"⏱️  Total review time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
        
        # Generate summary
        self.generate_review_summary(file_reviews)
        
        # Submit review if changes are requested
        self._submit_review(file_reviews)
        
        # Add PR link to JIRA ticket (optional)
        if self.jira_issue and self.jira_key:
            pr_url = f"https://github.com/{self.repo_name}/pull/{self.pr_number}"
            self.jira_service.add_pr_comment(self.jira_key, pr_url, self.pr_title)
        
        print("-" * 60)
        print("✅ AI Code Review Complete!")
        print(f"📝 Reviewed {len(file_reviews)} files")
        print(f"💬 Check the PR for detailed comments and suggestions")

if __name__ == "__main__":
    try:
        reviewer = AICodeReviewer()
        reviewer.run()
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

