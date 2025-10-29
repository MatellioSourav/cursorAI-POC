#!/usr/bin/env python3
"""
Demo file for AI Code Review - Contains intentional issues for demonstration
This file will be reviewed automatically when merged to main branch.
"""

# Security Issue: Hardcoded credentials
DATABASE_PASSWORD = "password123"
API_KEY = "sk-abcdef123456789"

def process_user_input(user_input):
    """Process user input - SQL injection vulnerability"""
    import sqlite3
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # CRITICAL SECURITY: SQL Injection
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result

# Bug: Division by zero
def calculate_average(numbers):
    """Calculate average - missing error handling"""
    total = sum(numbers)
    count = len(numbers)
    return total / count  # Will crash if count is 0

# Performance: Inefficient algorithm
def find_duplicates(data):
    """Find duplicates - O(n²) complexity"""
    duplicates = []
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j]:
                duplicates.append(data[i])
    return duplicates

# Code Quality: No type hints, poor naming
def x(a, b):
    """Unclear function name and purpose"""
    result = a + b * 2
    return result

# Missing: Error handling, documentation, tests

if __name__ == "__main__":
    # Test the functions
    user_data = process_user_input("admin")
    print(f"User: {user_data}")
    
    avg = calculate_average([1, 2, 3, 4, 5])
    print(f"Average: {avg}")

