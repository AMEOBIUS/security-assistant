"""
Base utilities for CI/CD integration.

Common logging and output formatting utilities shared across CLI modules.
"""

import logging
import sys
from typing import Any

__version__ = "1.0.0"


def get_logger(name: str) -> logging.Logger:
    """Get logger with given name."""
    return logging.getLogger(name)


def get_version_info() -> str:
    """Get version information."""
    return __version__


def print_banner(banner: str, width: int = 60) -> None:
    """Print banner with decorative border."""
    border = "=" * width
    print(f"\n{border}")
    for line in banner.split("\n"):
        print(line.center(width))
    print(f"{border}")


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"\033[92m{message}\033[0m")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"\033[91mError: {message}\033[0m")
    print(file=sys.stderr, flush=True)


def print_info(message: str) -> None:
    """Print info message in blue."""
    print(f"\033[94m{message}\033[0m")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(f"\033[93mWarning: {message}\033[0m")


def print_json(obj: Any, indent: int = 2) -> None:
    """Print JSON object with optional indentation."""
    import json
    print(json.dumps(obj, indent=indent))


def escape_ansi(text: str) -> str:
    """Remove ANSI color codes from text."""
    import re
    ansi_escape = re.compile(r'\033\[[0-9;]*[mK]')
    return ansi_escape.sub('', text)
