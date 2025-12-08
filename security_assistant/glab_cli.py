"""
GitLab CLI Integration for Security Assistant

Provides wrapper functions for glab CLI commands to create issues,
manage merge requests, and interact with GitLab from Python.

Requirements:
    - glab CLI installed (brew install glab)
    - Authenticated (glab auth login)
"""

import subprocess
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GlabIssue:
    """GitLab issue created via glab CLI"""
    iid: int
    title: str
    url: str
    state: str


class GlabCLIError(Exception):
    """Raised when glab CLI command fails"""
    pass


class GlabCLI:
    """Wrapper for glab CLI commands"""
    
    def __init__(self):
        """Initialize glab CLI wrapper"""
        if not self._is_glab_installed():
            raise GlabCLIError(
                "glab CLI is not installed. Install it from: "
                "https://gitlab.com/gitlab-org/cli"
            )
        
        logger.info("Initialized GlabCLI wrapper")
    
    def _is_glab_installed(self) -> bool:
        """Check if glab CLI is installed"""
        try:
            subprocess.run(
                ["glab", "version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _run_command(self, args: List[str]) -> str:
        """
        Run glab CLI command
        
        Args:
            args: Command arguments (e.g., ["issue", "list"])
        
        Returns:
            Command output as string
        
        Raises:
            GlabCLIError: If command fails
        """
        cmd = ["glab"] + args
        logger.debug(f"Running glab command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise GlabCLIError(f"glab command failed: {e.stderr}")
    
    def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        confidential: bool = True,
        assignee: Optional[str] = None,
    ) -> GlabIssue:
        """
        Create GitLab issue using glab CLI
        
        Args:
            title: Issue title
            description: Issue description
            labels: List of labels
            confidential: Make issue confidential (default: True)
            assignee: Assignee username
        
        Returns:
            GlabIssue with created issue details
        
        Example:
            >>> cli = GlabCLI()
            >>> issue = cli.create_issue(
            ...     title="[Security] CVE-2021-12345",
            ...     description="Found in alpine:3.15",
            ...     labels=["security", "critical"]
            ... )
            >>> print(issue.url)
        """
        args = [
            "issue", "create",
            "-t", title,
            "-d", description,
        ]
        
        if labels:
            args.extend(["-l", ",".join(labels)])
        
        if confidential:
            args.append("--confidential")
        
        if assignee:
            args.extend(["-a", assignee])
        
        output = self._run_command(args)
        
        # Parse output to extract issue details
        # Example output: "https://gitlab.com/group/project/-/issues/123"
        url = output.strip().split()[-1]
        iid = int(url.split("/")[-1])
        
        return GlabIssue(
            iid=iid,
            title=title,
            url=url,
            state="opened"
        )
    
    def list_issues(
        self,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        state: str = "opened",
    ) -> List[Dict]:
        """
        List GitLab issues
        
        Args:
            assignee: Filter by assignee (@me for current user)
            labels: Filter by labels
            state: Filter by state (opened, closed, all)
        
        Returns:
            List of issue dictionaries
        """
        args = ["issue", "list", "--state", state]
        
        if assignee:
            args.extend(["--assignee", assignee])
        
        if labels:
            args.extend(["--label", ",".join(labels)])
        
        output = self._run_command(args)
        
        # Parse output (glab returns table format by default)
        # For structured data, we could use --output json if available
        return []  # Simplified for now
    
    def create_merge_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
    ) -> str:
        """
        Create merge request using glab CLI
        
        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            title: MR title
            description: MR description
            labels: List of labels
        
        Returns:
            MR URL
        """
        args = [
            "mr", "create",
            "--source-branch", source_branch,
            "--target-branch", target_branch,
            "-t", title,
            "-d", description,
        ]
        
        if labels:
            args.extend(["-l", ",".join(labels)])
        
        output = self._run_command(args)
        return output.strip().split()[-1]
    
    def duo_ask(self, question: str) -> str:
        """
        Ask GitLab Duo a question via glab CLI
        
        Args:
            question: Question to ask
        
        Returns:
            Duo's response
        
        Example:
            >>> cli = GlabCLI()
            >>> answer = cli.duo_ask("How to revert last commit?")
            >>> print(answer)
        """
        args = ["duo", "ask", question]
        return self._run_command(args)
    
    def get_pipeline_status(self, pipeline_id: Optional[int] = None) -> str:
        """
        Get CI/CD pipeline status
        
        Args:
            pipeline_id: Pipeline ID (optional, uses latest if not provided)
        
        Returns:
            Pipeline status
        """
        args = ["ci", "view"]
        
        if pipeline_id:
            args.append(str(pipeline_id))
        
        return self._run_command(args)


# Example usage
if __name__ == "__main__":
    # Initialize CLI
    cli = GlabCLI()
    
    # Create security issue
    issue = cli.create_issue(
        title="[Security] CVE-2021-12345 in alpine:3.15",
        description="Critical vulnerability found in OpenSSL",
        labels=["security", "critical", "trivy"],
        confidential=True
    )
    
    print(f"Created issue: {issue.url}")
    
    # Ask GitLab Duo
    answer = cli.duo_ask("How to scan Docker image for vulnerabilities?")
    print(f"Duo says: {answer}")
