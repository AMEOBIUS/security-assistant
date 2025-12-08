"""
GitLab API Integration Module
Handles communication with GitLab API for issue creation and management.
Includes rate limiting, retry logic, and comprehensive error handling.
"""

import os
import time
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

# Checked: requests@2.31.0+ (Nov 2025) - no critical CVEs, stable
# Latest: 2.32.3 available (minor update, not critical)
import requests
from requests.adapters import HTTPAdapter

# Checked: urllib3@2.0.0+ (Nov 2025) - stable, no critical CVEs
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """
    Rate limiting configuration.
    
    GitLab.com limits (as of 2025):
    - POST /projects/:id/issues: No specific limit (general API limit applies)
    - GET /projects: 2000 requests per 10 minutes
    - GET /projects/:id: 400 requests per minute
    - General authenticated API: ~2000 requests per hour
    
    Our defaults (50/min, 2000/hour) are conservative and safe for all operations,
    especially issue creation which is our primary use case.
    
    For self-managed GitLab instances, these limits can be customized via
    ApplicationSettings API or admin UI.
    
    References:
    - https://docs.gitlab.com/security/rate_limits/
    - https://about.gitlab.com/blog/rate-limitations-announced-for-projects-groups-and-users-apis/
    """
    max_requests_per_minute: int = 50
    max_requests_per_hour: int = 2000
    retry_after_seconds: int = 60


@dataclass
class IssueData:
    """Data structure for GitLab issue."""
    title: str
    description: str
    labels: Optional[List[str]] = None
    assignee_ids: Optional[List[int]] = None
    confidential: bool = True
    due_date: Optional[str] = None


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.minute_requests: List[float] = []
        self.hour_requests: List[float] = []
    
    def _clean_old_requests(self):
        """Remove requests older than tracking window."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self.minute_requests = [t for t in self.minute_requests if t > minute_ago]
        self.hour_requests = [t for t in self.hour_requests if t > hour_ago]
    
    def can_make_request(self) -> bool:
        """Check if request can be made within rate limits."""
        self._clean_old_requests()
        
        if len(self.minute_requests) >= self.config.max_requests_per_minute:
            return False
        if len(self.hour_requests) >= self.config.max_requests_per_hour:
            return False
        
        return True
    
    def wait_if_needed(self):
        """Wait if rate limit is reached."""
        while not self.can_make_request():
            logger.warning("Rate limit reached, waiting...")
            time.sleep(1)
    
    def record_request(self):
        """Record a new request."""
        now = time.time()
        self.minute_requests.append(now)
        self.hour_requests.append(now)


class GitLabAPIError(Exception):
    """Base exception for GitLab API errors."""
    pass


class GitLabAuthError(GitLabAPIError):
    """Authentication error."""
    pass


class GitLabRateLimitError(GitLabAPIError):
    """Rate limit exceeded error."""
    pass


class GitLabAPI:
    """
    GitLab API client with rate limiting and error handling.
    
    Features:
    - Automatic rate limiting
    - Retry logic with exponential backoff
    - Comprehensive error handling
    - Session management with connection pooling
    """
    
    def __init__(
        self,
        gitlab_url: Optional[str] = None,
        private_token: Optional[str] = None,
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        """
        Initialize GitLab API client.
        
        Args:
            gitlab_url: GitLab instance URL (default: from GITLAB_URL env)
            private_token: GitLab private token (default: from GITLAB_TOKEN env)
            rate_limit_config: Rate limiting configuration
        """
        self.gitlab_url = gitlab_url or os.getenv("GITLAB_URL", "https://gitlab.com")
        self.private_token = private_token or os.getenv("GITLAB_TOKEN")
        
        if not self.private_token:
            raise GitLabAuthError("GitLab token not provided. Set GITLAB_TOKEN environment variable.")
        
        self.api_url = f"{self.gitlab_url}/api/v4"
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        
        # Configure session with retry logic
        self.session = self._create_session()
        
        logger.info(f"GitLab API client initialized for {self.gitlab_url}")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "PRIVATE-TOKEN": self.private_token,
            "Content-Type": "application/json"
        })
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make API request with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/projects/123/issues')
            data: Request body data
            params: Query parameters
            
        Returns:
            Response JSON data
            
        Raises:
            GitLabAPIError: On API errors
            GitLabAuthError: On authentication errors
            GitLabRateLimitError: On rate limit errors
        """
        # Wait if rate limit reached
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            logger.debug(f"{method} {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            
            # Record successful request
            self.rate_limiter.record_request()
            
            # Handle response
            if response.status_code == 401:
                raise GitLabAuthError("Authentication failed. Check your GitLab token.")
            
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise GitLabRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")
            
            if response.status_code >= 400:
                error_msg = response.json().get("message", response.text) if response.text else "Unknown error"
                raise GitLabAPIError(f"API error ({response.status_code}): {error_msg}")
            
            return response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            raise GitLabAPIError("Request timeout. GitLab API is not responding.")
        except requests.exceptions.ConnectionError:
            raise GitLabAPIError(f"Connection error. Cannot reach {self.gitlab_url}")
        except requests.exceptions.RequestException as e:
            raise GitLabAPIError(f"Request failed: {str(e)}")
    
    def create_issue(
        self,
        project_id: str,
        issue_data: IssueData
    ) -> Dict[str, Any]:
        """
        Create a new issue in GitLab project.
        
        Args:
            project_id: GitLab project ID or path (e.g., 'namespace/project')
            issue_data: Issue data
            
        Returns:
            Created issue data
            
        Example:
            >>> api = GitLabAPI()
            >>> issue = IssueData(
            ...     title="Security: SQL Injection in login.py",
            ...     description="**Severity:** High\\n\\n**File:** login.py:42",
            ...     labels=["security", "bug"],
            ...     confidential=True
            ... )
            >>> result = api.create_issue("my-group/my-project", issue)
            >>> print(f"Issue created: {result['web_url']}")
        """
        endpoint = f"/projects/{requests.utils.quote(project_id, safe='')}/issues"
        
        payload = {
            "title": issue_data.title,
            "description": issue_data.description,
            "confidential": issue_data.confidential
        }
        
        if issue_data.labels:
            payload["labels"] = ",".join(issue_data.labels)
        
        if issue_data.assignee_ids:
            payload["assignee_ids"] = issue_data.assignee_ids
        
        if issue_data.due_date:
            payload["due_date"] = issue_data.due_date
        
        logger.info(f"Creating issue in project {project_id}: {issue_data.title}")
        
        try:
            result = self._make_request("POST", endpoint, data=payload)
            logger.info(f"Issue created successfully: {result.get('web_url')}")
            return result
        except GitLabAPIError as e:
            logger.error(f"Failed to create issue: {str(e)}")
            raise
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project information.
        
        Args:
            project_id: GitLab project ID or path
            
        Returns:
            Project data
        """
        endpoint = f"/projects/{requests.utils.quote(project_id, safe='')}"
        logger.info(f"Fetching project info: {project_id}")
        return self._make_request("GET", endpoint)
    
    def list_issues(
        self,
        project_id: str,
        labels: Optional[List[str]] = None,
        state: str = "opened"
    ) -> List[Dict[str, Any]]:
        """
        List issues in a project.
        
        Args:
            project_id: GitLab project ID or path
            labels: Filter by labels
            state: Issue state (opened, closed, all)
            
        Returns:
            List of issues
        """
        endpoint = f"/projects/{requests.utils.quote(project_id, safe='')}/issues"
        
        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)
        
        logger.info(f"Listing issues for project {project_id}")
        return self._make_request("GET", endpoint, params=params)
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
            logger.info("GitLab API session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
