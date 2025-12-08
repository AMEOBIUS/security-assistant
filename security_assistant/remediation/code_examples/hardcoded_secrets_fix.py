# VULNERABLE:
# api_key = "EXAMPLE_API_KEY_VALUE"
# db_password = "EXAMPLE_PASSWORD_VALUE"

# SECURE:
import os

# Load from environment variables
api_key = os.environ.get("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable not set")

db_password = os.environ.get("DB_PASSWORD")
