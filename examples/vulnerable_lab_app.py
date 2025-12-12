#!/usr/bin/env python3
"""
Vulnerable Lab Application for Security Testing

⚠️ WARNING: This application contains INTENTIONAL security vulnerabilities
for educational and testing purposes ONLY. DO NOT use in production!

Vulnerabilities included:
- Command Injection (subprocess.run with shell=True)
- Code Injection (eval)
- Unsafe Deserialization (pickle.loads)
- SQL Injection

This is used by test_shellcode_integration.py to verify security scanning capabilities.
"""

import pickle
import sqlite3
import subprocess


class VulnerableLabApp:
    """
    Intentionally vulnerable application for security testing.
    
    ⚠️ DO NOT USE IN PRODUCTION ⚠️
    """
    
    def __init__(self):
        self.db_path = ":memory:"
        self.api_key = "hardcoded_secret_key_12345"  # Hardcoded secret vulnerability
        self._setup_database()
    
    def _setup_database(self):
        """Setup in-memory SQLite database for testing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                email TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin@example.com")
        )
        conn.commit()
        conn.close()
    
    # VULNERABILITY 1: Command Injection
    def execute_system_command(self, user_input):
        """
        ⚠️ VULNERABLE: Command injection via shell=True
        
        This allows arbitrary command execution through user input.
        Example exploit: user_input = "ls; cat /etc/passwd"
        """
        # INTENTIONAL VULNERABILITY - DO NOT USE IN PRODUCTION
        result = subprocess.run(
            user_input,
            shell=True,  # ⚠️ VULNERABILITY: shell=True enables command injection
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    
    # VULNERABILITY 2: Code Injection
    def evaluate_expression(self, expression):
        """
        ⚠️ VULNERABLE: Code injection via eval()
        
        This allows arbitrary Python code execution.
        Example exploit: expression = "__import__('os').system('whoami')"
        """
        # INTENTIONAL VULNERABILITY - DO NOT USE IN PRODUCTION
        try:
            result = eval(expression)  # ⚠️ VULNERABILITY: eval() enables code injection
            return result
        except Exception as e:
            return f"Error: {e}"
    
    # VULNERABILITY 3: Unsafe Deserialization
    def deserialize_data(self, serialized_data):
        """
        ⚠️ VULNERABLE: Unsafe deserialization via pickle.loads
        
        This allows arbitrary code execution through crafted pickle data.
        Example exploit: Craft malicious pickle payload with __reduce__
        """
        # INTENTIONAL VULNERABILITY - DO NOT USE IN PRODUCTION
        try:
            data = pickle.loads(serialized_data)  # ⚠️ VULNERABILITY: pickle.loads is unsafe
            return data
        except Exception as e:
            return f"Error: {e}"
    
    # VULNERABILITY 4: SQL Injection
    def get_user_by_username(self, username):
        """
        ⚠️ VULNERABLE: SQL injection via string concatenation
        
        This allows arbitrary SQL queries.
        Example exploit: username = "admin' OR '1'='1"
        """
        # INTENTIONAL VULNERABILITY - DO NOT USE IN PRODUCTION
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ⚠️ VULNERABILITY: String concatenation in SQL query
        query = f"SELECT * FROM users WHERE username = '{username}'"
        cursor.execute(query)
        
        result = cursor.fetchall()
        conn.close()
        return result


def main():
    """
    Main function demonstrating vulnerable operations.
    
    ⚠️ FOR TESTING ONLY - DO NOT USE IN PRODUCTION ⚠️
    """
    print("=" * 60)
    print("⚠️  VULNERABLE LAB APPLICATION - FOR TESTING ONLY  ⚠️")
    print("=" * 60)
    print()
    print("This application contains intentional security vulnerabilities")
    print("for educational and testing purposes.")
    print()
    print("Vulnerabilities included:")
    print("  1. Command Injection (subprocess.run with shell=True)")
    print("  2. Code Injection (eval)")
    print("  3. Unsafe Deserialization (pickle.loads)")
    print("  4. SQL Injection")
    print()
    print("=" * 60)
    
    app = VulnerableLabApp()
    
    # Example usage (safe examples for demonstration)
    print("\n📋 Example Operations:")
    print(f"  - API Key: {app.api_key[:10]}... (hardcoded)")
    print()
    print("✅ Lab environment initialized successfully")
    print("⚠️  Remember: This is for TESTING ONLY!")


if __name__ == "__main__":
    main()
