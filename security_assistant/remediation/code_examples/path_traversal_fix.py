# VULNERABLE:
# filename = user_input
# with open("/var/www/uploads/" + filename, "r") as f: ...

# SECURE:
import os

BASE_DIR = "/var/www/uploads"
filename = user_input
# 1. Join path
full_path = os.path.join(BASE_DIR, filename)
# 2. Normalize path
real_path = os.path.realpath(full_path)

# 3. Verify it is still within BASE_DIR
if not real_path.startswith(os.path.realpath(BASE_DIR)):
    raise ValueError("Path traversal attempt detected")

with open(real_path, "r") as f:
    data = f.read()
