#!/usr/bin/env python3
"""
JIRA Service Module - Fetches JIRA ticket details via Internal Webhook API
Uses: http://hrm.matellio.com/api/jira/getissuedetail/{project_id}/{jira_key}
"""

import os
import re
import requests
from typing import Optional, Dict, List


class JiraService:
    """Service for interacting with Internal JIRA Webhook API"""
    
    def __init__(self):
        # Internal API configuration
        self.api_base_url = os.getenv('JIRA_API_BASE_URL', 'http://hrm.matellio.com/api/jira').rstrip('/')
        self.project_id = os.getenv('JIRA_PROJECT_ID', '')
        
        # Check if configuration is available
        if not self.project_id:
            print("⚠️  JIRA_PROJECT_ID not configured. JIRA-aware reviews will be skipped.")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ JIRA integration enabled - Project ID: {self.project_id}")
    
    def extract_jira_key(self, text: str) -> Optional[str]:
        """
        Extract JIRA issue key from text using regex: [A-Z][A-Z0-9]+-[0-9]+
        
        Args:
            text: Text to search (branch name, PR title, commit message)
            
        Returns:
            First JIRA key found or None
        """
        # Pattern: PROJECT-123 (e.g., H30-22552, PROJ-123, ABC-456)
        pattern = r'[A-Z][A-Z0-9]+-[0-9]+'
        matches = re.findall(pattern, text.upper())
        
        if matches:
            # Return the first match (most common case)
            return matches[0]
        return None
    
    def find_jira_key(self, branch_name: str, pr_title: str, commit_messages: list) -> Optional[str]:
        """
        Search for JIRA key in branch name, PR title, and commit messages
        
        Args:
            branch_name: Git branch name
            pr_title: Pull request title
            commit_messages: List of commit messages
            
        Returns:
            JIRA key if found, None otherwise
        """
        # Priority: PR title > branch name > commit messages
        sources = [
            ("PR title", pr_title),
            ("branch name", branch_name),
        ]
        
        # Add commit messages
        for i, msg in enumerate(commit_messages[:5]):  # Check first 5 commits
            sources.append((f"commit message {i+1}", msg))
        
        for source_name, text in sources:
            jira_key = self.extract_jira_key(text)
            if jira_key:
                print(f"✅ Found JIRA key {jira_key} in {source_name}")
                return jira_key
        
        return None
    
    def fetch_issue(self, issue_key: str) -> Optional[Dict]:
        """
        Fetch JIRA issue details using Internal Webhook API
        
        Endpoint: GET /getissuedetail/{project_id}/{jira_key}
        Example: GET /getissuedetail/1554/H30-22552
        
        Args:
            issue_key: JIRA issue key (e.g., H30-22552)
            
        Returns:
            Dictionary with issue details or None if error
        """
        if not self.enabled:
            return None
        
        try:
            # Build API URL: http://hrm.matellio.com/api/jira/getissuedetail/{project_id}/{jira_key}
            url = f"{self.api_base_url}/getissuedetail/{self.project_id}/{issue_key}"
            
            print(f"🔍 Fetching JIRA issue {issue_key} from internal API...")
            print(f"   URL: {url}")
            
            # No authentication needed for internal API
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                api_response = response.json()
                
                # Check response status
                if api_response.get('status') == 'error':
                    error_msg = api_response.get('message', 'Unknown error')
                    print(f"⚠️  JIRA API returned error: {error_msg}")
                    return None
                
                # Extract data from success response
                if api_response.get('status') == 'success' and 'data' in api_response:
                    issue_data = api_response['data']
                    return self._normalize_issue(issue_data, issue_key)
                else:
                    print(f"⚠️  Unexpected API response format")
                    return None
                    
            else:
                print(f"⚠️  Error fetching JIRA issue: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', response.text[:200])
                    print(f"   Error message: {error_msg}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout fetching JIRA issue {issue_key} (exceeded 15s)")
            return None
        except Exception as e:
            print(f"⚠️  Exception fetching JIRA issue: {str(e)}")
            return None
    
    def _normalize_issue(self, issue_data: Dict, issue_key: str) -> Dict:
        """
        Normalize internal API response into review-friendly structure
        
        Response format:
        {
          "status": "success",
          "data": {
            "id": "37113",
            "key": "H30-22552",
            "summary": "...",
            "description": "...",
            "subtasks": [
              { "id": "37119", "key": "H30-22558", "summary": "..." }
            ]
          }
        }
        
        Args:
            issue_data: Raw API response data object
            issue_key: JIRA issue key (for URL construction)
            
        Returns:
            Normalized issue dictionary
        """
        # Extract basic fields
        summary = issue_data.get('summary', '')
        description = issue_data.get('description', '')
        
        # Extract subtasks
        subtasks = issue_data.get('subtasks', [])
        subtask_list = []
        if subtasks:
            for subtask in subtasks:
                subtask_list.append({
                    'key': subtask.get('key', ''),
                    'summary': subtask.get('summary', ''),
                    'id': subtask.get('id', '')
                })
        
        # Extract acceptance criteria from description
        acceptance_criteria = self._extract_acceptance_criteria_from_description(description)
        
        return {
            'key': issue_data.get('key', issue_key),
            'id': issue_data.get('id', ''),
            'summary': summary,
            'description': description or '',
            'acceptance_criteria': acceptance_criteria or '',
            'subtasks': subtask_list,
            'issue_type': '',  # Not provided by internal API
            'priority': '',   # Not provided by internal API
            'status': '',     # Not provided by internal API
            'url': f"https://vidocqstudios.atlassian.net/browse/{issue_data.get('key', issue_key)}"
        }
    
    def _extract_acceptance_criteria_from_description(self, description: str) -> Optional[str]:
        """
        Extract acceptance criteria section from description
        
        Args:
            description: Full description text
            
        Returns:
            Acceptance criteria text or None
        """
        if not description:
            return None
        
        # Common patterns for acceptance criteria
        patterns = [
            r'Acceptance Criteria[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'AC[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'Acceptance[:\s]*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'Acceptance\s+Criteria[:\s]*(.*?)(?=\n\n|\n#|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no explicit section found, return full description as acceptance criteria
        # (as per requirement: "Treat description as the primary source of acceptance criteria")
        return description.strip() if description.strip() else None
    
    def add_pr_comment(self, issue_key: str, pr_url: str, pr_title: str) -> bool:
        """
        Add PR link as comment on JIRA ticket
        
        NOTE: This feature is disabled for internal API as it doesn't support
        writing comments. The internal API is read-only.
        
        Args:
            issue_key: JIRA issue key
            pr_url: PR URL
            pr_title: PR title
            
        Returns:
            False (feature not available with internal API)
        """
        # Internal API doesn't support writing comments
        print(f"ℹ️  PR linking to JIRA not available with internal API (read-only)")
        return False
