# NoSQL Injection Remediation

## Description
NoSQL injection attacks exploit vulnerabilities in NoSQL databases (like MongoDB) where user input is passed directly to database queries, allowing attackers to manipulate the query logic.

## Remediation
1.  **Sanitize Input**: Ensure input is a string, not an object or array (which can be interpreted as query operators).
2.  **Use ODMs**: Use Object Document Mappers (like Mongoose) with built-in schema validation.
3.  **Avoid `$where`**: Do not use the `$where` operator in MongoDB, as it executes JavaScript.
4.  **Least Privilege**: Run the database with minimal permissions.
