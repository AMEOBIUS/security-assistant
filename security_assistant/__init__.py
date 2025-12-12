"""
Security Assistant - GitLab Integration Module
Automated security vulnerability management for GitLab projects.
"""

# Load environment variables from .env file
from pathlib import Path

from dotenv import load_dotenv

from .gitlab_api import GitLabAPI

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

__version__ = "0.1.0"
__author__ = "Security Assistant Team"

__all__ = ["GitLabAPI"]
