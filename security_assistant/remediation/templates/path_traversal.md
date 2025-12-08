# Path Traversal Remediation

## Description
Path Traversal involves exploiting insufficient security validation/sanitization of user-supplied input file names, so that characters representing "traverse to parent directory" are passed through to the file APIs.

## Remediation
1. **Avoid Direct File Access**: Do not use user input directly in file paths.
2. **Normalize Paths**: Use `os.path.abspath` and `os.path.realpath` to resolve paths before checking them.
3. **Chroot Jail**: Run the process in a restricted directory environment.
4. **Validate Against Base Directory**: Ensure the resolved path starts with the expected base directory.
5. **Use Indirect References**: Use an ID or token mapped to a file instead of the filename itself.
