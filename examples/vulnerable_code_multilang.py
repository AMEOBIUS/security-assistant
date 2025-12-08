"""
Multi-language vulnerable code examples for Semgrep testing.
This file contains intentional security vulnerabilities for demonstration.

WARNING: DO NOT use this code in production!
"""

# ============================================================================
# PYTHON VULNERABILITIES
# ============================================================================

import os
import pickle
import subprocess
import hashlib
from flask import Flask, request

app = Flask(__name__)

# B105: Hardcoded password
def connect_to_database():
    password = "admin123"  # Hardcoded password
    api_key = "sk-1234567890abcdef"  # Hardcoded API key
    return f"postgresql://user:{password}@localhost/db"

# B307: Use of eval()
def calculate(expression):
    result = eval(expression)  # Dangerous: arbitrary code execution
    return result

# B602: Shell injection
def run_user_command(user_input):
    os.system(user_input)  # Dangerous: command injection
    subprocess.call(user_input, shell=True)  # Also dangerous

# B301: Pickle deserialization
def load_user_data(data):
    user = pickle.loads(data)  # Dangerous: arbitrary code execution
    return user

# B608: SQL injection
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
    query2 = "SELECT * FROM users WHERE name = '%s'" % request.args.get('name')
    return query

# B201: Flask debug mode
@app.route('/debug')
def debug_route():
    app.run(debug=True)  # Dangerous in production

# B104: Binding to all interfaces
def start_server():
    app.run(host='0.0.0.0')  # Dangerous: exposed to internet

# B303: Insecure hash (MD5)
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # Weak hash

# B506: Unsafe YAML load
import yaml
def load_config(config_file):
    with open(config_file) as f:
        config = yaml.load(f)  # Dangerous: arbitrary code execution
    return config

# B324: Insecure hash (SHA1)
def hash_data(data):
    return hashlib.sha1(data.encode()).hexdigest()  # Weak hash

# B501: Request without certificate validation
import requests
def fetch_data(url):
    response = requests.get(url, verify=False)  # Dangerous: MITM attack
    return response.text

# B108: Hardcoded temp file
def write_temp():
    with open('/tmp/data.txt', 'w') as f:  # Predictable temp file
        f.write('sensitive data')

# B113: Request without timeout
def slow_request(url):
    response = requests.get(url)  # No timeout: DoS vulnerability
    return response

# B703: Django XSS
from django.utils.safestring import mark_safe
def render_user_input(user_input):
    return mark_safe(user_input)  # XSS vulnerability


# ============================================================================
# JAVASCRIPT/TYPESCRIPT VULNERABILITIES (in comments for Python file)
# ============================================================================

"""
// SQL Injection
const query = "SELECT * FROM users WHERE id = " + req.params.id;
db.query(query);

// XSS
app.get('/search', (req, res) => {
    res.send('<h1>Results for: ' + req.query.q + '</h1>');
});

// Command Injection
const exec = require('child_process').exec;
exec('ls ' + req.query.dir);

// Hardcoded credentials
const password = 'admin123';
const apiKey = 'sk-1234567890abcdef';

// Insecure random
Math.random(); // Not cryptographically secure

// Eval usage
eval(userInput);

// Prototype pollution
const obj = {};
obj[userInput] = value;

// Path traversal
const filePath = './uploads/' + req.query.file;
fs.readFile(filePath);

// Missing helmet
const express = require('express');
const app = express();
// No app.use(helmet())

// Cookie without httpOnly
res.cookie('session', token);

// CORS misconfiguration
app.use(cors({ origin: '*' }));

// Weak crypto
const crypto = require('crypto');
crypto.createHash('md5');

// Insecure JWT
jwt.sign(payload, 'secret');

// Missing rate limiting
app.post('/login', (req, res) => {
    // No rate limiting
});
"""


# ============================================================================
# GO VULNERABILITIES (in comments for Python file)
# ============================================================================

"""
package main

import (
    "crypto/md5"
    "database/sql"
    "fmt"
    "os/exec"
)

// Weak crypto
func hashPassword(password string) string {
    h := md5.New()
    h.Write([]byte(password))
    return fmt.Sprintf("%x", h.Sum(nil))
}

// SQL injection
func getUser(db *sql.DB, userID string) {
    query := "SELECT * FROM users WHERE id = " + userID
    db.Query(query)
}

// Command injection
func runCommand(cmd string) {
    exec.Command("sh", "-c", cmd).Run()
}

// Hardcoded credentials
const apiKey = "sk-1234567890abcdef"

// Insecure random
import "math/rand"
func generateToken() int {
    return rand.Int()
}

// Path traversal
func readFile(filename string) {
    filepath := "./uploads/" + filename
    ioutil.ReadFile(filepath)
}
"""


# ============================================================================
# JAVA VULNERABILITIES (in comments for Python file)
# ============================================================================

"""
// SQL Injection
String query = "SELECT * FROM users WHERE id = " + userId;
statement.executeQuery(query);

// Command Injection
Runtime.getRuntime().exec("ls " + userInput);

// Hardcoded password
String password = "admin123";

// Weak crypto
MessageDigest md = MessageDigest.getInstance("MD5");

// Insecure random
Random random = new Random();

// XXE vulnerability
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
// No dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);

// Deserialization
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();

// Path traversal
String filePath = "./uploads/" + fileName;
new File(filePath);

// LDAP injection
String filter = "(&(uid=" + username + ")(userPassword=" + password + "))";
"""


if __name__ == "__main__":
    print("This file contains intentional vulnerabilities for testing.")
    print("DO NOT use this code in production!")
    print("\nVulnerabilities included:")
    print("- Hardcoded credentials")
    print("- Command injection")
    print("- SQL injection")
    print("- Insecure deserialization")
    print("- Weak cryptography")
    print("- XSS vulnerabilities")
    print("- And more...")
