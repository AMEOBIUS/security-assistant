# Vulnerable Lab Environment

A deliberately vulnerable web application for practicing offensive security skills.
**WARNING: DO NOT RUN THIS ON A PUBLIC SERVER. USE ONLY IN ISOLATED ENVIRONMENTS.**

## Features

1.  **SQL Injection:** Vulnerable search and login forms.
2.  **Reflected XSS:** Vulnerable comments section.
3.  **Command Injection:** Vulnerable ping utility.
4.  **Broken Access Control:** Admin panel access.

## Quick Start (Docker)

The safest way to run this lab is using Docker.

```bash
cd examples/vulnerable_lab
docker-compose up --build
```

Access the lab at `http://localhost:5000`.

## Manual Start (Not Recommended)

```bash
pip install -r requirements.txt
python app.py
```

## Challenge

Try to find the flag in the Admin panel!
Hint: The admin user is `admin`. You can bypass authentication using SQL Injection.
