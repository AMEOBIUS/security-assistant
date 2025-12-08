"""
Security Assistant - GitLab Integration Module
Automated security vulnerability management for GitLab projects.
"""

__version__ = "0.1.0"
__author__ = "Security Assistant Team"

from .gitlab_api import GitLabAPI

__all__ = ["GitLabAPI"]
