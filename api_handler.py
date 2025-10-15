#!/usr/bin/env python3
"""
API Handler Module - REST API endpoints with various issues for AI to detect
"""

import json
import requests
from datetime import datetime

class APIHandler:
    """API request handler with multiple code quality and security issues"""
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.api_key = "hardcoded-api-key-12345"  # SECURITY: Hardcoded API key!
        self.cache = {}
    
    def fetch_user_data(self, user_id):
        """Fetch user data from API - Multiple issues"""
        
        # SECURITY: API key exposed in URL
        url = f"{self.base_url}/users/{user_id}?api_key={self.api_key}"
        
        # BUG: No error handling for network failures
        response = requests.get(url)
        
        # BUG: No status code check
        data = response.json()
        
        return data
    
    def update_user(self, user_id, user_data):
        """Update user via API - Dangerous implementation"""
        
        url = f"{self.base_url}/users/{user_id}"
        
        # SECURITY: No input validation on user_data
        # BUG: No timeout set, could hang forever
        response = requests.put(url, json=user_data)
        
        return response.status_code == 200
    
    def batch_fetch_users(self, user_ids):
        """Fetch multiple users - Performance issues"""
        
        users = []
        
        # PERFORMANCE: N+1 problem - making separate API call for each user
        for user_id in user_ids:
            user = self.fetch_user_data(user_id)
            users.append(user)
        
        return users
    
    def search_users(self, query):
        """Search users - Inefficient caching"""
        
        # PERFORMANCE: Cache check is inefficient
        cache_key = query
        if cache_key in self.cache:
            # BUG: No cache expiration, stale data forever
            return self.cache[cache_key]
        
        url = f"{self.base_url}/search?q={query}"  # SECURITY: No URL encoding
        response = requests.get(url)
        results = response.json()
        
        self.cache[cache_key] = results
        return results


def process_webhook(webhook_data):
    """Process incoming webhook - Critical security issues"""
    
    # SECURITY: No webhook signature verification!
    # SECURITY: No rate limiting
    # BUG: No input validation
    
    event_type = webhook_data['type']  # BUG: Could cause KeyError
    payload = webhook_data['payload']
    
    # CODE QUALITY: No logging
    # BUG: No error handling
    
    if event_type == 'user.created':
        user_id = payload['id']
        email = payload['email']
        
        # SECURITY: Sensitive data in logs (if logging was added)
        print(f"New user: {email}")
        
        return True
    
    return False


def parse_api_response(response_text):
    """Parse API response - Vulnerable to attacks"""
    
    # SECURITY: eval() is EXTREMELY dangerous!
    # This allows arbitrary code execution
    try:
        data = eval(response_text)
        return data
    except:
        # CODE QUALITY: Bare except, swallowing all errors
        # BUG: No error logging
        return None


class DataProcessor:
    """Process API data - Boilerplate and design issues"""
    
    def __init__(self):
        self.users = []
        self.posts = []
        self.comments = []
    
    # BOILERPLATE: Repetitive CRUD operations
    def add_user(self, user):
        self.users.append(user)
    
    def remove_user(self, user):
        self.users.remove(user)  # BUG: Will raise ValueError if not found
    
    def add_post(self, post):
        self.posts.append(post)
    
    def remove_post(self, post):
        self.posts.remove(post)
    
    def add_comment(self, comment):
        self.comments.append(comment)
    
    def remove_comment(self, comment):
        self.comments.remove(comment)
    
    # PERFORMANCE: Inefficient search - O(n) every time
    def find_user_posts(self, user_id):
        user_posts = []
        for post in self.posts:
            if post['user_id'] == user_id:
                user_posts.append(post)
        return user_posts
    
    # PERFORMANCE: Nested loops - O(n²)
    def get_posts_with_comments(self):
        result = []
        for post in self.posts:
            post_data = post.copy()
            post_data['comments'] = []
            for comment in self.comments:
                if comment['post_id'] == post['id']:
                    post_data['comments'].append(comment)
            result.append(post_data)
        return result


def make_api_request(url, method='GET', data=None):
    """Make API request - Poor implementation"""
    
    # BUG: No timeout
    # BUG: No retry logic
    # BUG: No error handling
    # SECURITY: No SSL verification control
    
    if method == 'GET':
        resp = requests.get(url)
    elif method == 'POST':
        resp = requests.post(url, data=data)
    elif method == 'PUT':
        resp = requests.put(url, data=data)
    else:
        # BUG: Returns None for unsupported methods
        return None
    
    # BUG: No status code validation
    return resp.text


# TESTING ISSUE: No unit tests for API functions
# TESTING ISSUE: No integration tests
# TESTING ISSUE: No mock objects for testing

if __name__ == "__main__":
    # SECURITY: Using hardcoded credentials
    api = APIHandler("https://api.example.com")
    
    # This will trigger multiple AI warnings!
    user = api.fetch_user_data(123)
    print(user)
    
    # Testing dangerous eval function
    malicious_input = "__import__('os').system('ls')"
    result = parse_api_response(malicious_input)  # DANGER!

