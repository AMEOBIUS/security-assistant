import os
import subprocess

def ping(host):
    # Command injection vulnerability
    subprocess.call("ping " + host, shell=True)

def get_secret():
    # Hardcoded secret (Example for testing scanners)
    api_key = "EXAMPLE_KEY_FOR_TESTING_ONLY_DO_NOT_USE"
    return api_key
