#!/usr/bin/env python3
"""
Performance issues demo - Contains intentional performance problems
"""

def find_duplicates_slow(data):
    """Find duplicates - O(n²) complexity"""
    # PERFORMANCE: Inefficient nested loops
    seen = set()
    duplicates = set()
    for i in range(len(data)):
        if data[i] in seen:
            duplicates.add(data[i])
        else:
            seen.add(data[i])
    return list(duplicates)

def get_user_orders(user_id):
    """Get user orders - N+1 query problem"""
    import sqlite3
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    # Get orders
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    orders = cursor.fetchall()
    
    # PERFORMANCE: N+1 problem - fetching items one by one
    result = []
    for order in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order[0],))
        items = cursor.fetchall()
        result.append({'order': order, 'items': items})
    
    conn.close()
    return result

def process_large_dataset(data):
    """Process dataset - inefficient operations"""
    # PERFORMANCE: Converting list to set and back unnecessarily
    unique_items = list(set(data))
    sorted_items = sorted(unique_items)
    
    # PERFORMANCE: Multiple passes through data
    return [x * 2 for x in sorted_items if x > 0]



