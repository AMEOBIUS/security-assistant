"""
CLI Base Module

Common utilities for CLI commands:
- Logging setup
- Argument parsing helpers
- Output formatting
"""

import logging
import sys
from pathlib import Path
from typing import Optional

__version__ = "1.0.0"


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Enable verbose output
        log_file: Path to log file
    """
    level = logging.DEBUG if verbose else logging.INFO

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers)


def print_banner():
    """Print Security Assistant banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          Security Assistant - CLI Interface               ║
╚═══════════════════════════════════════════════════════════╝
""")


def print_error(message: str):
    """Print error message in red."""
    print(f"\033[91mError: {message}\033[0m", file=sys.stderr)


def print_success(message: str):
    """Print success message in green."""
    print(f"\033[92m{message}\033[0m")


def print_warning(message: str):
    """Print warning message in yellow."""
    print(f"\033[93mWarning: {message}\033[0m")


def print_info(message: str):
    """Print info message in blue."""
    print(f"\033[94m{message}\033[0m")


def validate_path(path: str) -> Path:
    """
    Validate and return Path object.
    
    Args:
        path: Path string to validate
        
    Returns:
        Path object
        
    Raises:
        ValueError: If path doesn't exist
    """
    p = Path(path)
    if not p.exists():
        raise ValueError(f"Path does not exist: {path}")
    return p


def get_logger(name: str) -> logging.Logger:
    """Get logger with given name."""
    return logging.getLogger(name)
