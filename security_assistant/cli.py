#!/usr/bin/env python3
"""
Security Assistant CLI - Command-line interface (refactored).

This is the main entry point that imports and uses modular command implementations.

Usage:
    security-assistant scan [OPTIONS] [TARGET]
    security-assistant config [OPTIONS]
    security-assistant report [OPTIONS]
    security-assistant --version
    security-assistant --help

Examples:
    # Basic scan
    security-assistant scan .

    # Scan with specific scanners
    security-assistant scan --bandit --semgrep src/

    # Scan with custom config
    security-assistant scan --config security-assistant.yaml

    # Generate reports only
    security-assistant report --format html,markdown

    # Create default config
    security-assistant config --create
"""

import sys

from security_assistant.cli import main

if __name__ == "__main__":
    sys.exit(main())
