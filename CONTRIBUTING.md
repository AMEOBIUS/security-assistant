# Contributing to Security Assistant

First off, thanks for taking the time to contribute!

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- Ensure the bug was not already reported.
- Open a new Issue with a clear title and description.
- Include a reproduction script or steps.

### Suggesting Enhancements

- Open a new Issue with the "enhancement" label.
- Explain why this enhancement would be useful.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints.
5. Submit the PR!

## Development Setup

```bash
git clone https://github.com/your-org/security-assistant.git
cd security-assistant
python -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

## Testing

```bash
pytest tests/
```
