#!/usr/bin/env python3
"""
Authentication helper module - Contains multiple security and code quality issues
for AI code review testing.
"""

import hashlib
import json
import os
from datetime import datetime

# Security Issue: Weak password hashing
def hash_password(password):
    """Hash password using MD5 - INSECURE"""
    # CRITICAL: MD5 is broken and should never be used for passwords
    return hashlib.md5(password.encode()).hexdigest()

# Security Issue: Hardcoded JWT secret
JWT_SECRET = "my-secret-key-12345"

def verify_token(token):
    """Verify JWT token - has security issues"""
    import jwt
    
    try:
        # Security: Using hardcoded secret, should use environment variable
        # Security: No algorithm specified (algorithm confusion attack possible)
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return decoded
    except:
        # Bug: Silent failure, no logging or proper error handling
        return None

def authenticate_user(username, password):
    """Authenticate user - multiple security issues"""
    # Security: SQL injection vulnerability
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # CRITICAL SECURITY: SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    
    # Bug: No password hashing comparison
    # Security: Returns raw user data without sanitization
    return user

# Performance Issue: Inefficient database queries
def get_user_profile(user_id):
    """Fetch user profile - N+1 query problem"""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Get user
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    # N+1 Problem: Fetching related data in loops
    # Performance: Should use JOIN or batch queries
    cursor.execute("SELECT * FROM posts WHERE user_id = ?", (user_id,))
    posts = cursor.fetchall()
    
    for post in posts:
        # N+1 Problem: Fetching comments for each post
        cursor.execute("SELECT * FROM comments WHERE post_id = ?", (post[0],))
        comments = cursor.fetchall()
    
    conn.close()
    return {"user": user, "posts": posts}

# Code Quality: Repetitive code, no DRY principle
def validate_email(email):
    if '@' in email and '.' in email:
        return True
    return False

def validate_phone(phone):
    if len(phone) == 10 and phone.isdigit():
        return True
    return False

def validate_username(username):
    if len(username) >= 3 and username.isalnum():
        return True
    return False

# Boilerplate: Repetitive validation pattern - should be abstracted

# Security: Sensitive data in logs
def log_user_action(user_id, action):
    """Log user action - security issue with sensitive data"""
    # Security: Logging potentially sensitive user data
    log_entry = f"[{datetime.now()}] User {user_id} performed action: {action}"
    print(log_entry)  # Should use proper logging framework
    # Security: No log sanitization or masking

# Missing: Type hints throughout
# Missing: Proper error handling
# Missing: Unit tests

def create_session(user):
    """Create user session - security and design issues"""
    # Security: Weak session token generation
    import random
    session_token = ''.join([str(random.randint(0, 9)) for _ in range(32)])
    
    # Bug: No expiration time set
    # Security: Using random instead of secrets module
    # Design: Session should be stored in database/Redis, not just returned
    
    return {
        "token": session_token,
        "user_id": user["id"],
        "username": user["username"]
    }

# Code Quality: Magic numbers
def check_password_strength(password):
    """Check password strength - poor implementation"""
    # Code Quality: Magic numbers (8, 1, 1, 1) should be constants
    if len(password) >= 8:
        if any(c.isupper() for c in password):
            if any(c.islower() for c in password):
                if any(c.isdigit() for c in password):
                    return True
    return False

# Testing Issue: No test coverage
# Design Issue: Functions are tightly coupled
# Documentation: Missing docstrings for complex logic

if __name__ == "__main__":
    # Example usage
    password = "mypassword123"
    hashed = hash_password(password)
    print(f"Hashed password: {hashed}")
    
    # This will have multiple issues caught by AI
    user = authenticate_user("admin", "password")
    print(f"User: {user}")

