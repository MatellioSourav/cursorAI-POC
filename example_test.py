#!/usr/bin/env python3
"""
Example test file to demonstrate AI code review capabilities.
Create a PR with this file to see the AI reviewer in action!
"""

def calculate_total(prices):
    """Calculate total price with some intentional issues for AI to catch"""
    total = 0
    for price in prices:
        # Issue: No validation of price type or value
        total = total + price
    return total


def get_user_by_id(user_id):
    """Fetch user from database - has SQL injection vulnerability"""
    import sqlite3
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Security Issue: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result


def process_data(data):
    """Process data with performance issues"""
    results = []
    
    # Performance Issue: Inefficient nested loops
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                results.append(data[i])
    
    return results


class UserManager:
    """User management with boilerplate code"""
    
    def __init__(self):
        self.users = []
    
    # Boilerplate Issue: Repetitive CRUD operations
    def add_user(self, user):
        self.users.append(user)
        
    def remove_user(self, user):
        self.users.remove(user)
        
    def find_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user
        return None


# Code Quality Issue: No error handling
def divide_numbers(a, b):
    return a / b


# Testing Issue: No unit tests for this module


if __name__ == "__main__":
    # This will trigger multiple AI review suggestions!
    prices = [10, 20, 30]
    total = calculate_total(prices)
    print(f"Total: {total}")
    
    user = get_user_by_id(1)
    print(f"User: {user}")

