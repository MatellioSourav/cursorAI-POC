#!/usr/bin/env python3
"""
Security vulnerabilities demo - Contains intentional security issues
"""

# CRITICAL: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_SECRET_KEY = "sk-1234567890abcdef"

def authenticate_user(username, password):
    """Authenticate user - SQL injection vulnerability"""
    import sqlite3
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # CRITICAL SECURITY: SQL Injection
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    
    user = cursor.fetchone()
    conn.close()
    return user

def hash_password(password):
    """Hash password - using weak MD5"""
    import hashlib
    # SECURITY: MD5 is broken, should use bcrypt/argon2
    return hashlib.md5(password.encode()).hexdigest()



