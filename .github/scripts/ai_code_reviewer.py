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
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.review_comments: List[ReviewComment] = []
        
        # Initialize JIRA service
        self.jira_service = JiraService()
        self.jira_issue = None
        self.jira_key = None
        
    def get_pr_diff(self) -> List[FileDiff]:
        """Get the diff of files changed in the PR"""
        print("🔍 Fetching PR changes...")
        
        # Get list of changed files
        cmd = f"git diff --name-status {self.base_sha} {self.head_sha}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
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
            
            # Get the diff for this file
            diff_cmd = f"git diff {self.base_sha} {self.head_sha} -- {filename}"
            diff_result = subprocess.run(diff_cmd, shell=True, capture_output=True, text=True)
            
            # Count additions and deletions
            additions = len([l for l in diff_result.stdout.split('\n') if l.startswith('+')])
            deletions = len([l for l in diff_result.stdout.split('\n') if l.startswith('-')])
            
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
            '.env', '.env.local', '.env.production'
        ]
        
        return any(pattern in filename for pattern in skip_patterns)
    
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
        """Build AI prompt with JIRA context if available"""
        jira_context = self._build_jira_context()
        
        # Get list of all changed files for scope check
        changed_files = [fd.filename for fd in getattr(self, '_all_file_diffs', [])]
        
        # Build base prompt
        prompt = f"""You are an expert code reviewer. Review the following code changes and provide constructive feedback.

{jira_context if jira_context else ""}

## CODE CHANGES

**File:** {file_diff.filename}
**Status:** {file_diff.status}
**Changes:** +{file_diff.additions} -{file_diff.deletions}

**All Changed Files in PR:**
{chr(10).join(f"- {f}" for f in changed_files)}

**DIFF:**
{file_diff.patch}

**FULL FILE CONTENT:**
{file_content[:10000]}  # Limit to first 10k chars

## REVIEW REQUIREMENTS

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
9. **Performance**: Inefficient algorithms, unnecessary operations, optimization opportunities
10. **Boilerplate Reduction**: Identify repetitive code that can be abstracted or simplified
11. **Design Patterns**: Suggest better architectural patterns if applicable
12. **Testing**: Missing test cases or testability issues

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
      "category": "requirement|quality|bug|security|performance|boilerplate|design|testing|scope",
      "title": "Brief issue title",
      "description": "Detailed explanation",
      "suggestion": "Specific recommendation or code example"
    }}
  ],
  "positive_aspects": ["List of good practices found in the code"]
}}

**IMPORTANT:**
- If acceptance criteria are missing or violated, mark severity as "error" and set final_verdict to "Changes Requested"
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
            system_message = "You are an expert code reviewer with deep knowledge of software engineering best practices, security, and design patterns."
            if self.jira_issue:
                system_message += " You are also an expert at evaluating code implementations against JIRA ticket requirements and acceptance criteria. You must strictly verify that code changes align with the specified requirements."
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4 Turbo (you can update to GPT-5 when available)
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
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
            for _, review in file_reviews:
                if review:
                    all_issues.extend(review.get('issues', []))
            
            critical_issues = [i for i in all_issues if i.get('severity') == 'error' and i.get('category') in ['requirement', 'scope']]
            
            review_body = "## ⚠️ Changes Requested\n\n"
            review_body += "This PR does not fully meet the JIRA ticket requirements:\n\n"
            
            for issue in critical_issues[:5]:  # Limit to 5 issues
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
            
            summary += f"\n### 📄 `{file_diff.filename}`\n\n"
            summary += f"**Overall Assessment**: {review.get('overall_assessment', 'No assessment provided')}\n\n"
            
            if review.get('positive_aspects'):
                summary += "**✨ Positive Aspects**:\n"
                for aspect in review['positive_aspects']:
                    summary += f"- {aspect}\n"
                summary += "\n"
            
            if review.get('issues'):
                summary += f"**Issues Found** ({len(review['issues'])}):\n\n"
                
                for i, issue in enumerate(review['issues'], 1):
                    emoji_map = {
                        'quality': '🎨',
                        'bug': '🐛',
                        'security': '🔒',
                        'performance': '⚡',
                        'boilerplate': '♻️',
                        'design': '🏗️',
                        'testing': '🧪'
                    }
                    emoji = emoji_map.get(issue.get('category', ''), '💡')
                    
                    summary += f"{i}. {emoji} **{issue['title']}**"
                    if issue.get('line'):
                        summary += f" (Line {issue['line']})"
                    summary += f"\n   - {issue['description']}\n"
                    if issue.get('suggestion'):
                        summary += f"   - 💡 *Suggestion*: {issue['suggestion']}\n"
                    summary += "\n"
        
        summary += "\n---\n"
        summary += "*This review was automatically generated using AI. Please review the suggestions and use your judgment.*\n"
        summary += "\n**Note to Team Lead**: The AI has performed the initial review. Please focus on the critical and warning items, and verify the suggestions align with your project's standards.\n"
        
        # Save summary to file
        with open('review_summary.md', 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print("✅ Review summary saved to review_summary.md")
    
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
        """Post comment asking for JIRA ticket link"""
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
        
        # Review each file
        file_reviews = []
        # Store file_diffs for use in prompt building
        self._all_file_diffs = file_diffs
        for file_diff in file_diffs:
            review = self.review_file(file_diff)
            if review:
                file_reviews.append((file_diff, review))
                self.post_review_comments(file_diff, review)
        
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

