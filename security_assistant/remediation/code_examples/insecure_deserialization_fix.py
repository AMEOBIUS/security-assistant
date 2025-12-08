# VULNERABLE:
# import pickle
# data = pickle.loads(user_input)  # RCE risk!

# SECURE (JSON):
import json

try:
    data = json.loads(user_input)
except json.JSONDecodeError:
    print("Invalid JSON")

# SECURE (YAML):
import yaml

try:
    # Always use safe_load, never load() or full_load() on untrusted input
    data = yaml.safe_load(user_input)
except yaml.YAMLError:
    print("Invalid YAML")
