"""
Example vulnerable Python code for testing Bandit scanner.
This file intentionally contains security vulnerabilities for demonstration.

WARNING: This code is intentionally insecure. DO NOT use in production!
"""

import os
import pickle
import subprocess


# B105: Hardcoded password
def authenticate_user():
    """Authenticate user with hardcoded credentials."""
    admin_password = "admin123"  # Hardcoded password
    api_key = "sk-1234567890abcdef"  # Hardcoded API key
    
    if user_input == admin_password:
        return True
    return False


# B307: Use of eval()
def calculate_expression(user_input):
    """Calculate mathematical expression from user input."""
    result = eval(user_input)  # Dangerous use of eval()
    return result


# B602: Shell injection
def run_command(filename):
    """Run shell command with user input."""
    os.system(f"cat {filename}")  # Shell injection vulnerability


# B301: Pickle deserialization
def load_user_data(data):
    """Load user data from pickle."""
    user_obj = pickle.loads(data)  # Unsafe deserialization
    return user_obj


# B608: SQL injection
def get_user_by_id(user_id):
    """Get user from database."""
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
    return execute_query(query)


# B201: Flask debug mode
def start_flask_app():
    """Start Flask application."""
    from flask import Flask
    app = Flask(__name__)
    app.run(debug=True)  # Debug mode in production


# B104: Binding to all interfaces
def start_server():
    """Start server on all interfaces."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 8080))  # Binding to all interfaces


# B303: Insecure hash function
def hash_password(password):
    """Hash password using MD5."""
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()  # Weak hash


# B506: YAML load
def load_config(config_file):
    """Load YAML configuration."""
    import yaml
    with open(config_file) as f:
        config = yaml.load(f)  # Unsafe YAML load
    return config


# B608: Hardcoded SQL with string formatting
def delete_user(username):
    """Delete user from database."""
    query = "DELETE FROM users WHERE username = '%s'" % username  # SQL injection
    return execute_query(query)


# Helper function (not vulnerable)
def execute_query(query):
    """Execute database query."""
    # Placeholder for database execution
    pass


if __name__ == "__main__":
    print("This file contains intentional security vulnerabilities for testing.")
    print("Run: bandit vulnerable_code.py")
