# VULNERABLE:
# import os
# os.system("ping " + host)

# SECURE (using subprocess):
import subprocess

# subprocess.run with shell=False treats the input as a single argument,
# preventing command injection.
subprocess.run(["ping", "-c", "1", host], shell=False, check=True)
