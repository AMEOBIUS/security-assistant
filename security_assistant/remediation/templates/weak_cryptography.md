# Weak Cryptography Remediation

## Description
Using weak encryption algorithms or hashing functions (like MD5 or SHA1) allows attackers to decrypt data or create collisions. Using non-cryptographically secure random number generators for security contexts makes secrets predictable.

## Remediation
1. **Use Strong Hashing**: Use algorithms like SHA-256 or SHA-512 for integrity, and Argon2, bcrypt, or PBKDF2 for passwords.
2. **Use Strong Encryption**: Use AES-256-GCM or ChaCha20-Poly1305.
3. **Secure Randomness**: Use `secrets` module in Python (or `os.urandom`) instead of `random`.
4. **Avoid Home-Rolled Crypto**: Always use established libraries (e.g., `cryptography` in Python).
