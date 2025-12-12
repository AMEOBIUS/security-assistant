from flask import Flask, request, render_template_string, redirect, url_for, session
import sqlite3
import os
import subprocess
import shlex

# CONFIGURATION (Loaded from environment for security)
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "default_insecure_key_for_dev")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

app = Flask(__name__)
app.secret_key = SECRET_KEY

def init_db():
    conn = sqlite3.connect('lab.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, content TEXT)''')
    # Add a dummy user
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', ?)", (ADMIN_PASSWORD,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '''
    <h1>Vulnerable Lab</h1>
    <ul>
        <li><a href="/search">SQL Injection (Search)</a></li>
        <li><a href="/comments">XSS (Comments)</a></li>
        <li><a href="/ping">Command Injection (Ping)</a></li>
        <li><a href="/admin">Broken Access Control (Admin)</a></li>
    </ul>
    '''

# 1. SQL Injection
@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    if query:
        conn = sqlite3.connect('lab.db')
        c = conn.cursor()
        # VULNERABLE: Direct string formatting
        try:
            sql = f"SELECT username FROM users WHERE username LIKE '%{query}%'"
            c.execute(sql)
            results = c.fetchall()
        except Exception as e:
            results = [f"Error: {e}"]
        conn.close()
    
    return f'''
    <h2>User Search</h2>
    <form><input name="q" value="{query}"><input type="submit" value="Search"></form>
    <ul>
        {''.join(f'<li>{r[0]}</li>' for r in results)}
    </ul>
    '''

# 2. Reflected XSS
@app.route('/comments', methods=['GET', 'POST'])
def comments():
    if request.method == 'POST':
        content = request.form.get('content')
        # VULNERABLE: Storing without sanitization
        conn = sqlite3.connect('lab.db')
        c = conn.cursor()
        c.execute("INSERT INTO comments (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()
        return redirect(url_for('comments'))
    
    conn = sqlite3.connect('lab.db')
    c = conn.cursor()
    c.execute("SELECT content FROM comments")
    comments_list = c.fetchall()
    conn.close()
    
    # VULNERABLE: render_template_string without autoescaping context, or manual formatting
    # Flask autoescapes templates, but we'll use manual string formatting to simulate vuln
    comments_html = ''.join(f"<div>{c[0]}</div>" for c in comments_list)
    
    return f'''
    <h2>Comments</h2>
    <form method="POST"><input name="content"><input type="submit" value="Post"></form>
    <div id="comments">
        {comments_html} 
    </div>
    '''

# 3. Command Injection
@app.route('/ping')
def ping():
    target = request.args.get('target', '')
    output = ""
    if target:
        # VULNERABLE: Shell=True with user input
        # Windows compatibility note: ping needs -n, linux needs -c
        count_flag = "-n" if os.name == 'nt' else "-c"
        try:
            cmd = f"ping {count_flag} 1 {target}"
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError as e:
            output = e.output.decode()
        except Exception as e:
            output = str(e)
            
    return f'''
    <h2>Ping Tool</h2>
    <form><input name="target" value="{target}"><input type="submit" value="Ping"></form>
    <pre>{output}</pre>
    '''

# 4. Broken Access Control / IDOR
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect('lab.db')
        c = conn.cursor()
        # VULNERABLE: Another SQLi opportunity
        c.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('admin'))
        else:
            return "Invalid credentials"
            
    return '''
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br>
        <input name="password" type="password" placeholder="Password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/admin')
def admin():
    # VULNERABLE: Weak check, no role verification
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    return f'''
    <h2>Admin Panel</h2>
    <p>Welcome, {session.get('username')}!</p>
    <p>Flag: CTF{{Y0U_AR3_ADM1N_N0W}}</p>
    <a href="/logout">Logout</a>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    # Bind to 0.0.0.0 to be accessible outside container
    app.run(host='0.0.0.0', port=5000, debug=False)
