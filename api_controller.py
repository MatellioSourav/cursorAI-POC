#!/usr/bin/env python3
"""
API Controller module - REST API endpoints with security, performance, and code quality issues
for comprehensive AI code review testing.
"""

from flask import Flask, request, jsonify, session
import os
import hashlib
import json
import subprocess
from functools import wraps

app = Flask(__name__)

# Security Issue: Weak secret key
app.secret_key = "my-secret-key-12345"

# Security Issue: CORS enabled for all origins
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Security Issue: Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Performance Issue: No caching configuration
# Code Quality: Missing configuration management

def require_auth(f):
    """Authentication decorator - has security issues"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Security: Token validation is weak
        # Security: No token expiration check
        # Bug: Token stored in session without proper validation
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Security: Token verification is too simplistic
        # Bug: No actual JWT validation, just checking if exists
        if token == "Bearer valid-token":
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid token"}), 401
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint - multiple security vulnerabilities"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Security: No input sanitization
    # Security: Password sent in plain text
    # Security: No rate limiting for login attempts
    # Bug: No validation of input parameters
    
    # Security: SQL injection vulnerability
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # CRITICAL: SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Security: Session token not cryptographically secure
        # Security: No session expiration
        session['user_id'] = user[0]
        session['username'] = username
        
        return jsonify({
            "message": "Login successful",
            "token": "Bearer valid-token",
            "user_id": user[0]
        })
    else:
        # Security: Timing attack vulnerability (different response times)
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get user details - security and privacy issues"""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Security: No authorization check (user can access other users' data)
    # Security: SQL injection risk (though mitigated by int conversion)
    # Bug: No check if user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Security: Returning password hash (should never expose)
        # Privacy: Returning all user data without filtering
        return jsonify({
            "id": user[0],
            "username": user[1],
            "password": user[2],  # SECURITY ISSUE: Exposing password hash
            "email": user[3],
            "role": user[4],
            "balance": user[5]  # Privacy: Financial data exposure
        })
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users/<int:user_id>/delete', methods=['DELETE'])
@require_auth
def delete_user(user_id):
    """Delete user - security and audit issues"""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Security: No authorization check (any authenticated user can delete anyone)
    # Security: No admin role verification
    # Bug: No soft delete, hard delete without backup
    # Security: No audit logging
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    # Security: No confirmation of deletion
    # Bug: No error handling if deletion fails
    return jsonify({"message": "User deleted"})

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    """File upload endpoint - security vulnerabilities"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # Security: No file type validation
    # Security: No file size limit
    # Security: No filename sanitization
    # Security: Upload to web-accessible directory
    # Bug: No error handling for disk full
    
    filename = file.filename  # SECURITY: Using unsanitized filename
    file.save(os.path.join('/var/www/uploads', filename))
    
    # Security: No virus scanning
    # Security: No content validation
    return jsonify({"message": "File uploaded", "filename": filename})

@app.route('/api/search', methods=['GET'])
def search():
    """Search endpoint - security and performance issues"""
    query = request.args.get('q')
    
    # Security: No input validation
    # Security: No rate limiting
    # Performance: No caching
    
    import sqlite3
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    
    # CRITICAL: SQL Injection
    # Performance: No full-text search, uses LIKE with wildcards
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
    cursor.execute(sql)
    results = cursor.fetchall()
    conn.close()
    
    # Performance: Returning all results without pagination
    # Bug: No limit on result size
    return jsonify({"results": results})

@app.route('/api/execute', methods=['POST'])
@require_auth
def execute_command():
    """Command execution endpoint - CRITICAL SECURITY ISSUE"""
    data = request.get_json()
    command = data.get('command')
    
    # CRITICAL SECURITY: Command injection vulnerability
    # Never execute user input as shell commands!
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Security: Exposing command output (could leak sensitive info)
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })

@app.route('/api/data/export', methods=['GET'])
@require_auth
def export_data():
    """Data export endpoint - security and privacy issues"""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Security: No authorization check (any user can export all data)
    # Privacy: Exposing all user data
    # Security: No encryption of exported data
    cursor.execute("SELECT * FROM users")
    all_users = cursor.fetchall()
    conn.close()
    
    # Security: Returning sensitive data in JSON
    # Privacy: Including passwords, emails, financial data
    return jsonify({
        "users": [{
            "id": user[0],
            "username": user[1],
            "password": user[2],  # CRITICAL: Exposing passwords
            "email": user[3],
            "balance": user[5]
        } for user in all_users]
    })

# Code Quality: Repetitive error handling pattern
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Bug: No actual health check of services
    # Code Quality: Returns hardcoded response
    return jsonify({"status": "ok"})

@app.route('/api/stats', methods=['GET'])
def stats():
    """Statistics endpoint"""
    # Bug: No actual stats calculation
    return jsonify({"stats": "not implemented"})

# Boilerplate: Repetitive endpoint patterns without proper error handling

# Missing: Rate limiting middleware
# Missing: Request logging
# Missing: Input validation middleware
# Missing: Error handling middleware
# Missing: API versioning
# Missing: Swagger/OpenAPI documentation
# Missing: Unit tests
# Missing: Integration tests
# Missing: Security headers (HSTS, CSP, etc.)
# Missing: Proper logging framework

if __name__ == '__main__':
    # Security: Running in debug mode in production
    # Security: No HTTPS enforcement
    # Performance: Single-threaded, not production-ready
    app.run(debug=True, host='0.0.0.0', port=5000)

