#!/usr/bin/env python3
"""
Script to automatically create a Pull Request on GitHub
This automates the PR creation process using GitHub API
"""

import os
import sys
import requests
import json
import subprocess

def get_current_branch():
    """Get current git branch"""
    result = subprocess.run(['git', 'branch', '--show-current'], 
                          capture_output=True, text=True)
    return result.stdout.strip()

def get_base_branch():
    """Get base branch (usually main or master)"""
    return 'main'  # Change to 'master' if needed

def get_repo_info():
    """Get repository owner and name from git remote"""
    result = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                          capture_output=True, text=True)
    url = result.stdout.strip()
    
    # Parse SSH or HTTPS URL
    if url.startswith('git@'):
        # git@github.com:owner/repo.git
        parts = url.replace('git@github.com:', '').replace('.git', '').split('/')
        return parts[0], parts[1]
    elif url.startswith('https://'):
        # https://github.com/owner/repo.git
        parts = url.replace('https://github.com/', '').replace('.git', '').split('/')
        return parts[0], parts[1]
    else:
        raise ValueError(f"Unable to parse repository URL: {url}")

def create_pr(token, owner, repo, head_branch, base_branch, title, body):
    """Create a Pull Request using GitHub API"""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'title': title,
        'body': body,
        'head': head_branch,
        'base': base_branch
    }
    
    print(f"🚀 Creating PR: {title}")
    print(f"📝 From: {head_branch} → To: {base_branch}")
    print(f"📦 Repository: {owner}/{repo}")
    print("-" * 60)
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        pr_data = response.json()
        pr_url = pr_data['html_url']
        pr_number = pr_data['number']
        
        print(f"✅ PR created successfully!")
        print(f"🔗 PR URL: {pr_url}")
        print(f"📊 PR Number: #{pr_number}")
        print("\n" + "=" * 60)
        print("🎉 Your PR is ready! The AI code review will start automatically.")
        print("=" * 60)
        
        return pr_url, pr_number
    else:
        error_data = response.json()
        error_msg = error_data.get('message', 'Unknown error')
        errors = error_data.get('errors', [])
        
        print(f"❌ Failed to create PR")
        print(f"Status Code: {response.status_code}")
        print(f"Error: {error_msg}")
        
        if errors:
            print("Detailed errors:")
            for error in errors:
                print(f"  - {error}")
        
        return None, None

def main():
    """Main function"""
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ Error: GITHUB_TOKEN environment variable is required")
        print("\nTo set it up:")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Generate a new token with 'repo' permissions")
        print("3. Run: export GITHUB_TOKEN='your-token-here'")
        print("   Or add it to your .bashrc/.zshrc for persistence")
        sys.exit(1)
    
    # Get repository information
    try:
        owner, repo = get_repo_info()
    except Exception as e:
        print(f"❌ Error getting repository info: {e}")
        sys.exit(1)
    
    # Get branch information
    head_branch = get_current_branch()
    base_branch = get_base_branch()
    
    if not head_branch:
        print("❌ Error: Could not determine current branch")
        sys.exit(1)
    
    # PR details
    title = "Test AI Code Review Agent - Security & Performance Issues"
    
    body = """## 🤖 Testing AI Code Review Agent

This PR is specifically created to test the AI code review system with intentional code issues.

### 📁 Files Changed:
1. **example_test.py** - Updated with security vulnerabilities and bug issues
2. **auth_helper.py** - Authentication module with critical security flaws  
3. **database_utils.py** - Database utilities with SQL injection and performance issues
4. **api_controller.py** - REST API endpoints with critical security vulnerabilities

### 🎯 Issues Included for AI to Detect:

#### 🔒 Security Issues:
- Hardcoded API keys and JWT secrets
- SQL injection vulnerabilities (multiple instances)
- Command injection vulnerability
- Weak password hashing (MD5)
- Exposed sensitive data (passwords in exports)
- Missing input validation
- No authentication/authorization checks
- CORS misconfiguration

#### 🐛 Bug Issues:
- Division by zero errors
- Missing error handling
- Race conditions
- Resource leaks
- Transaction issues

#### ⚡ Performance Issues:
- N+1 query problems
- Inefficient algorithms (O(n²))
- No connection pooling
- Missing indexes
- No caching

#### 🎨 Code Quality Issues:
- Code duplication (DRY violations)
- Missing type hints
- Magic numbers
- Missing documentation
- No API versioning

### 📊 Expected AI Findings:
The AI reviewer should identify:
- Critical security vulnerabilities (20+)
- Performance bottlenecks (15+)
- Code quality improvements
- Best practice violations
- Testing gaps

### ✅ Purpose:
This PR is for testing the automated AI code review workflow. All issues are intentional to validate the AI reviewer's effectiveness.

---

**Note**: Once this PR is created, the GitHub Actions workflow will automatically trigger and the AI will review all files.
"""
    
    # Create the PR
    pr_url, pr_number = create_pr(
        github_token, 
        owner, 
        repo, 
        head_branch, 
        base_branch, 
        title, 
        body
    )
    
    if pr_url:
        # Open in browser (optional)
        import webbrowser
        webbrowser.open(pr_url)
        
        print(f"\n💡 Tip: Check the 'Actions' tab to see the AI review workflow progress")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

