# VULNERABLE (Hashing):
# import hashlib
# hash = hashlib.md5(password.encode()).hexdigest()

# SECURE (Hashing for passwords):
# pip install bcrypt
import bcrypt

# Hash a password
# salt = bcrypt.gensalt()
# hashed = bcrypt.hashpw(password.encode(), salt)

# VULNERABLE (Random):
# import random
# token = random.random()

# SECURE (Random):
import secrets
token = secrets.token_urlsafe(32)

# VULNERABLE (Encryption):
# DES, RC4, etc.

# SECURE (Encryption):
from cryptography.fernet import Fernet
key = Fernet.generate_key()
cipher_suite = Fernet(key)
cipher_text = cipher_suite.encrypt(b"Secret data")
plain_text = cipher_suite.decrypt(cipher_text)
