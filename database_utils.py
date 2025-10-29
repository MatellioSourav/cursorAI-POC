#!/usr/bin/env python3
"""
Database utilities module - Contains performance, security, and code quality issues
for comprehensive AI code review testing.
"""

import sqlite3
import json
import os
from typing import Any, Dict, List, Optional

# Security Issue: Database connection without connection pooling
# Performance Issue: No connection reuse
DB_PATH = "/tmp/database.db"

def get_connection():
    """Get database connection - has resource management issues"""
    # Bug: Connection not properly managed (no context manager)
    # Performance: Should use connection pooling
    # Security: No connection timeout set
    return sqlite3.connect(DB_PATH)

def insert_user(username: str, password: str, email: str):
    """Insert user - has security and error handling issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Security: Password not hashed before storage
    # Security: SQL injection risk if parameters not properly escaped
    # Bug: No validation of input parameters
    # Bug: No transaction handling
    cursor.execute(
        f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
    )
    
    # Bug: No error handling for duplicate usernames, constraint violations
    # Bug: Connection not closed in exception cases
    conn.commit()
    conn.close()

def get_users_by_role(role: str):
    """Get users by role - security and performance issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Security: SQL injection if role is user input
    # Performance: No LIMIT clause, could return huge dataset
    # Code Quality: No error handling
    query = f"SELECT * FROM users WHERE role = '{role}'"
    cursor.execute(query)
    
    users = cursor.fetchall()
    conn.close()
    
    # Bug: Returns raw tuples, should return dictionaries or objects
    # Security: Returns password hashes (should never expose)
    return users

def update_user_balance(user_id: int, amount: float):
    """Update user balance - race condition and transaction issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bug: Race condition - two concurrent requests can cause incorrect balance
    # Bug: No transaction isolation
    # Performance: Two queries instead of one
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    current_balance = cursor.fetchone()[0]
    
    # Bug: No validation of amount (could be negative, causing issues)
    new_balance = current_balance + amount
    
    cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    
    # Bug: No check if user exists before updating
    conn.commit()
    conn.close()

def delete_old_sessions():
    """Delete old sessions - performance and correctness issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Performance: Full table scan without proper indexing
    # Bug: Hardcoded date logic, should use proper date functions
    # Code Quality: Magic number (30) should be a constant
    cursor.execute("DELETE FROM sessions WHERE created_at < datetime('now', '-30 days')")
    
    # Bug: No logging of how many sessions deleted
    # Security: No audit trail
    conn.commit()
    conn.close()

def bulk_insert_products(products: List[Dict]):
    """Bulk insert products - performance and error handling issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Performance: Inserting one by one instead of batch insert
    # Bug: If one fails, all previous inserts are lost (no transaction)
    # Bug: No validation of product data
    for product in products:
        cursor.execute(
            "INSERT INTO products (name, price, category) VALUES (?, ?, ?)",
            (product.get('name'), product.get('price'), product.get('category'))
        )
    
    # Bug: Commit only at end, so if error occurs, all work is lost
    conn.commit()
    conn.close()

def search_products(query: str, limit: int = 100):
    """Search products - SQL injection and performance issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # CRITICAL SECURITY: SQL Injection vulnerability
    # Performance: LIKE query without proper indexing will be slow
    # Bug: No sanitization of search query
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%' LIMIT {limit}"
    cursor.execute(sql)
    
    results = cursor.fetchall()
    conn.close()
    
    # Bug: No pagination support beyond limit
    # Code Quality: Returns raw tuples
    return results

# Code Quality: Repetitive connection pattern
def get_user_count():
    """Get total user count"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_product_count():
    """Get total product count"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Boilerplate: Same pattern repeated - should use context manager or decorator

# Security: Exposing internal structure
def export_all_user_data():
    """Export all user data - major security issue"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # CRITICAL SECURITY: Exposing all user data including passwords
    # Security: No access control check
    # Security: Should never export passwords or sensitive data
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    conn.close()
    
    # Security: No encryption of exported data
    # Bug: Returns sensitive information
    return json.dumps([dict(zip(['id', 'username', 'password', 'email'], row)) for row in all_users])

def get_user_orders(user_id: int):
    """Get user orders - N+1 query problem"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get orders
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    
    # N+1 Problem: Fetching items for each order separately
    # Performance: Should use JOIN
    result = []
    for order in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order[0],))
        items = cursor.fetchall()
        result.append({'order': order, 'items': items})
    
    conn.close()
    return result

# Missing: Proper error handling throughout
# Missing: Logging framework
# Missing: Connection retry logic
# Missing: Database migration support
# Missing: Type hints in some functions
# Missing: Unit tests

if __name__ == "__main__":
    # Example usage - these will trigger multiple AI review findings
    insert_user("testuser", "plaintext123", "test@example.com")
    
    users = get_users_by_role("admin")
    print(f"Admin users: {users}")
    
    products = search_products("laptop")
    print(f"Found products: {products}")

