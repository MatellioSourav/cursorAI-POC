#!/usr/bin/env python3
"""
Authentication module - This file has intentional issues for AI to detect and review
"""

import sqlite3
import hashlib

def authenticate_user(username, password):
    """Authenticate user against database - HAS CRITICAL SECURITY ISSUES!"""
    
    # SECURITY ISSUE: SQL Injection vulnerability - user input directly in query
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    
    # BUG: No None check - will crash if user not found
    return user[0]


def validate_password(password):
    """Validate password strength - WEAK VALIDATION"""
    
    # CODE QUALITY ISSUE: Very weak password requirements
    if len(password) > 5:
        return True
    return False


def hash_password(password):
    """Hash password - INSECURE HASHING ALGORITHM"""
    
    # SECURITY ISSUE: MD5 is cryptographically broken, should use bcrypt or argon2
    return hashlib.md5(password.encode()).hexdigest()


def send_password_reset_email(email, token):
    """Send password reset email"""
    
    # SECURITY ISSUE: No rate limiting, vulnerable to email bombing
    # BUG: No email validation
    
    message = f"Reset your password: http://example.com/reset?token={token}"
    
    # Code just prints, doesn't actually send
    print(f"Email to {email}: {message}")
    return True


class UserSession:
    """User session management - Has performance and design issues"""
    
    def __init__(self):
        self.sessions = {}
        self.user_cache = []
    
    # PERFORMANCE ISSUE: O(n) lookup when should be O(1)
    def find_session(self, user_id):
        for session_id, data in self.sessions.items():
            if data['user_id'] == user_id:
                return session_id
        return None
    
    # PERFORMANCE ISSUE: Inefficient cache lookup
    def get_user_from_cache(self, user_id):
        for user in self.user_cache:
            if user['id'] == user_id:
                return user
        return None
    
    # BOILERPLATE: Repetitive session management code
    def create_session(self, user_id):
        import uuid
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user_id, 
            'created': True,
            'timestamp': 12345
        }
        return session_id
    
    def delete_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def update_session(self, session_id, data):
        if session_id in self.sessions:
            self.sessions[session_id].update(data)


def login(username, password):
    """Main login function - NO ERROR HANDLING!"""
    
    # BUG: No try-except, will crash on any error
    # BUG: No input validation
    # BUG: Password validated but not hashed before checking DB
    
    if validate_password(password):
        user = authenticate_user(username, password)
        return user
    
    return None


def register_user(username, password, email):
    """Register new user - MULTIPLE ISSUES"""
    
    # SECURITY: Storing plaintext password!
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # SECURITY: SQL Injection again
    query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
    cursor.execute(query)
    
    conn.commit()
    conn.close()
    
    # CODE QUALITY: Should return user object or ID
    return True


# TESTING ISSUE: No unit tests for ANY of these critical security functions!

if __name__ == "__main__":
    # This code will trigger MULTIPLE AI review warnings!
    user = login("admin", "123456")
    print(f"Logged in: {user}")
    
    # Testing with obvious SQL injection
    user2 = login("admin' OR '1'='1", "anything")
    print(f"Hacked: {user2}")

