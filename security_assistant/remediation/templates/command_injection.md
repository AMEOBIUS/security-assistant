# Command Injection Remediation

## Description
Command injection is an attack in which the goal is execution of arbitrary commands on the host operating system via a vulnerable application.

## Remediation
1. **Avoid Shell Execution**: Use language-specific APIs instead of spawning shell commands (e.g., use `subprocess.run` with `shell=False` in Python).
2. **Input Validation**: Strictly validate input against an allowlist of permitted characters.
3. **Parameterization**: If shell execution is unavoidable, ensure arguments are parameterized and not concatenated strings.
4. **Least Privilege**: Run the application with the minimum necessary privileges.
