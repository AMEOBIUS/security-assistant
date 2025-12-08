# SQL Injection Remediation

## Description
SQL Injection occurs when untrusted user input is directly concatenated into a database query.

## Remediation
1. Use parameterized queries (prepared statements) instead of string concatenation.
2. Validate and sanitize all user input.
3. Use an ORM that handles parameterization automatically.
4. Apply least privilege principle to database accounts.
