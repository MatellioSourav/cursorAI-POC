#!/usr/bin/env python3
"""
Post review summary to Bitbucket PR
"""

import os
import sys
import requests

def find_pr_id(workspace, repo_slug, branch, app_password):
    """Find PR ID by querying Bitbucket API using branch name"""
    if not branch:
        return None
    
    try:
        api_base = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"
        headers = {
            'Authorization': f'Bearer {app_password}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        prs_url = f"{api_base}/pullrequests?state=OPEN&pagelen=50"
        response = requests.get(prs_url, headers=headers)
        
        if response.status_code != 200:
            print(f"⚠️  Failed to fetch PRs: {response.status_code}")
            return None
        
        prs_data = response.json()
        prs = prs_data.get('values', [])
        
        for pr in prs:
            source_branch = pr.get('source', {}).get('branch', {}).get('name', '')
            if source_branch == branch:
                return str(pr.get('id'))
        
        return None
    except Exception as e:
        print(f"⚠️  Error finding PR ID: {str(e)}")
        return None

def post_summary():
    workspace = os.getenv('BITBUCKET_WORKSPACE')
    repo_slug = os.getenv('BITBUCKET_REPO_SLUG')
    pr_id = os.getenv('BITBUCKET_PR_ID')
    branch = os.getenv('BITBUCKET_BRANCH')
    username = os.getenv('BITBUCKET_USERNAME')
    app_password = os.getenv('BITBUCKET_APP_PASSWORD')
    
    if app_password:
        app_password = app_password.strip()
    
    if not all([workspace, repo_slug, app_password]):
        print("⚠️  Missing required Bitbucket environment variables")
        return
    
    # Detect token type
    token_preview = app_password[:4] if len(app_password) >= 4 else ""
    is_repository_access_token = token_preview == "ATB"  # Repository Access Token
    is_bitbucket_api_token = token_preview == "ATBB"  # Bitbucket API Token
    is_atlassian_token = token_preview == "ATAT"  # Atlassian API Token
    
    # Try to find PR ID if not set
    if not pr_id and branch:
        pr_id = find_pr_id(workspace, repo_slug, branch, app_password)
        if not pr_id:
            return
    elif not pr_id:
        return
    
    try:
        with open('review_summary.md', 'r', encoding='utf-8') as f:
            summary = f.read()
    except FileNotFoundError:
        print("⚠️  review_summary.md not found")
        return
    
    api_base = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"
    comments_url = f"{api_base}/pullrequests/{pr_id}/comments"
    
    # For Repository Access Tokens (ATB...), use Bearer authentication
    # For other tokens, try Basic Auth with username
    import base64
    headers = None
    test_url = f"{api_base}/pullrequests/{pr_id}"
    
    # Repository Access Tokens (ATB...) MUST use Bearer authentication
    if is_repository_access_token:
        headers = {
            'Authorization': f'Bearer {app_password}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        test_response = requests.get(test_url, headers=headers, timeout=10)
        if test_response.status_code != 200:
            headers = None
    
    # Try Basic Auth with username (for scoped tokens)
    if not headers and username:
        credentials = f"{username}:{app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        test_response = requests.get(test_url, headers=headers, timeout=10)
        if test_response.status_code == 200:
            pass  # Success!
        else:
            headers = None
    
    # If that failed, try Bearer token
    if not headers or (headers and test_response.status_code != 200):
        headers = {
            'Authorization': f'Bearer {app_password}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        test_response = requests.get(test_url, headers=headers, timeout=10)
        if test_response.status_code != 200:
            headers = None
    
    # If Bearer failed, try Basic Auth with workspace
    if not headers or (headers and test_response.status_code != 200):
        credentials = f"{workspace}:{app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        test_response = requests.get(test_url, headers=headers, timeout=10)
    
    # Final check
    if test_response.status_code == 401:
        print("❌ Authentication failed")
        if is_repository_access_token:
            print("   ⚠️  Repository Access Token (ATB...) authentication failed")
            print("   Verify token is valid and has required permissions")
        elif not username:
            print("   ⚠️  BITBUCKET_USERNAME not set - required for scoped API tokens")
            print("   Set BITBUCKET_USERNAME to your Bitbucket username (not email)")
        elif is_atlassian_token:
            print("   ⚠️  Atlassian tokens (ATATT...) may not work for PR comments")
            print("   💡 Use Repository Access Token (ATB...) instead:")
            print("   Repository Settings → Access tokens")
        return
    
    # Delete previous summary comments to prevent email spam
    try:
        response = requests.get(comments_url, headers=headers)
        if response.status_code == 200:
            comments_data = response.json()
            comments = comments_data.get('values', [])
            
            for comment in comments:
                content = comment.get('content', {}).get('raw', '')
                if '🤖 AI Code Review Summary' in content:
                    comment_id = comment.get('id')
                    if comment_id:
                        delete_url = f"{api_base}/pullrequests/{pr_id}/comments/{comment_id}"
                        delete_response = requests.delete(delete_url, headers=headers)
                        if delete_response.status_code in [200, 204]:
                            print("🗑️  Deleted previous summary comment")
                            break
    except Exception as e:
        print(f"⚠️  Could not delete previous summary: {str(e)}")
    
    # Post new summary as PR comment
    comment_data = {
        'content': {
            'raw': summary
        }
    }
    
    try:
        response = requests.post(comments_url, headers=headers, json=comment_data)
        if response.status_code in [200, 201]:
            print("✅ Posted review summary to PR")
        else:
            error_msg = response.text[:300] if response.text else "No error message"
            print(f"⚠️  Failed to post summary: {response.status_code} - {error_msg}")
            
            if response.status_code == 401:
                print("❌ Authentication failed (401). Check BITBUCKET_APP_PASSWORD token and scopes.")
    except Exception as e:
        print(f"⚠️  Error posting summary: {str(e)}")

if __name__ == "__main__":
    post_summary()