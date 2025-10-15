#!/usr/bin/env python3
"""
AI Code Reviewer - Automated code review using OpenAI GPT
This script analyzes pull request changes and provides intelligent code review suggestions.
"""

import os
import sys
import json
import subprocess
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests
from openai import OpenAI

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
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        self.review_comments: List[ReviewComment] = []
        
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
    
    def review_file(self, file_diff: FileDiff) -> Optional[Dict]:
        """Review a single file using AI"""
        print(f"📝 Reviewing {file_diff.filename}...")
        
        # Read the full file content if it exists
        try:
            with open(file_diff.filename, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except:
            file_content = "File not accessible or was deleted"
        
        prompt = f"""You are an expert code reviewer. Review the following code changes and provide constructive feedback.

File: {file_diff.filename}
Status: {file_diff.status}
Changes: +{file_diff.additions} -{file_diff.deletions}

DIFF:
{file_diff.patch}

FULL FILE CONTENT:
{file_content[:10000]}  # Limit to first 10k chars

Please provide a detailed code review focusing on:
1. **Code Quality**: Best practices, clean code principles, maintainability
2. **Potential Bugs**: Logic errors, edge cases, null pointer issues
3. **Security**: Vulnerabilities, injection risks, authentication/authorization issues
4. **Performance**: Inefficient algorithms, unnecessary operations, optimization opportunities
5. **Boilerplate Reduction**: Identify repetitive code that can be abstracted or simplified
6. **Design Patterns**: Suggest better architectural patterns if applicable
7. **Testing**: Missing test cases or testability issues

Format your response as JSON with the following structure:
{{
  "overall_assessment": "Brief summary of the changes",
  "severity": "info|warning|critical",
  "issues": [
    {{
      "line": <line_number or null>,
      "severity": "info|warning|error",
      "category": "quality|bug|security|performance|boilerplate|design|testing",
      "title": "Brief issue title",
      "description": "Detailed explanation",
      "suggestion": "Specific recommendation or code example"
    }}
  ],
  "positive_aspects": ["List of good practices found in the code"]
}}

Be constructive, specific, and helpful. Focus on meaningful improvements."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4 Turbo (you can update to GPT-5 when available)
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer with deep knowledge of software engineering best practices, security, and design patterns."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            review_result = json.loads(response.choices[0].message.content)
            return review_result
            
        except Exception as e:
            print(f"❌ Error reviewing {file_diff.filename}: {str(e)}")
            return None
    
    def post_review_comments(self, file_diff: FileDiff, review: Dict):
        """Post review comments to GitHub PR"""
        if not review or not review.get('issues'):
            return
        
        github_api_url = f"https://api.github.com/repos/{self.repo_name}/pulls/{self.pr_number}/comments"
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
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
            
            # Try to find the specific line in the diff
            line_number = issue.get('line')
            if line_number:
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
        
        summary = f"""# 🤖 AI Code Review Summary

## Overview
- **Files Reviewed**: {total_files}
- **Total Issues Found**: {total_issues}
  - 🔴 Critical: {critical_count}
  - ⚠️  Warnings: {warning_count}
  - ℹ️  Info: {info_count}

## Detailed Analysis

"""
        
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
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting AI Code Review...")
        print(f"📦 Repository: {self.repo_name}")
        print(f"🔀 PR #{self.pr_number}")
        print(f"📊 Comparing {self.base_sha[:7]} → {self.head_sha[:7]}")
        print("-" * 60)
        
        # Get PR diff
        file_diffs = self.get_pr_diff()
        
        if not file_diffs:
            print("ℹ️  No files to review")
            return
        
        print(f"📁 Found {len(file_diffs)} file(s) to review")
        print("-" * 60)
        
        # Review each file
        file_reviews = []
        for file_diff in file_diffs:
            review = self.review_file(file_diff)
            if review:
                file_reviews.append((file_diff, review))
                self.post_review_comments(file_diff, review)
        
        # Generate summary
        self.generate_review_summary(file_reviews)
        
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

