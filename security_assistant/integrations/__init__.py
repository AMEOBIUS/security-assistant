"""
Integrations package.

External service integrations (GitLab, GitHub, etc.)
"""

from security_assistant.integrations.gitlab_mr_creator import GitLabMRCreator

__all__ = ["GitLabMRCreator"]
