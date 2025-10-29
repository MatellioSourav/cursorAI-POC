#!/usr/bin/env python3
"""
Bug issues demo - Contains intentional bug issues
"""

def calculate_division(a, b):
    """Calculate division - missing error handling"""
    # BUG: Will crash if b is 0
    return a / b

def process_user_data(data):
    """Process user data - missing validation"""
    # BUG: No check if data is None or empty
    # BUG: No type checking
    result = []
    for item in data:
        result.append(item * 2)
    return result

def get_user_profile(user_id):
    """Get user profile - missing error handling"""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    # BUG: Connection not closed if exception occurs
    conn.close()
    
    # BUG: Will crash if user is None
    return {"username": user[1], "email": user[3]}

