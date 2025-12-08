# VULNERABLE:
# import re
# pattern = re.compile(r"(a+)+$")
# pattern.match("aaaaaaaaaaaaaaaaaaaaaaaaaaaaa!") # Hangs

# SECURE:
# 1. Limit input length
MAX_LEN = 100
if len(user_input) > MAX_LEN:
    raise ValueError("Input too long")

# 2. Use simple regex or third-party safe library
# pip install google-re2
# import re2
# pattern = re2.compile(r"(a+)+$")
# pattern.match(user_input) # Safe, fails fast
