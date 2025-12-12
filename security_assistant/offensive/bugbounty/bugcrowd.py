"""
Bugcrowd API Client

Integration with Bugcrowd platform for:
- Vulnerability submission
- Program information
- Bounty tracking
- Report management
"""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from security_assistant.offensive.authorization import AuthorizationService

logger = logging.getLogger(__name__)


class BugcrowdClient:
    """
    Bugcrowd API client for bug bounty operations.
    
    Args:
        api_token: Bugcrowd API token
        program_id: Bugcrowd program ID
        auth_service: Authorization service for ToS checking
    """
    
    BASE_URL = "https://api.bugcrowd.com"
    
    def __init__(
        self,
        api_token: str,
        program_id: str,
        auth_service: Optional[AuthorizationService] = None
    ):
        self.api_token = api_token
        self.program_id = program_id
        self.auth_service = auth_service or AuthorizationService()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"BugcrowdClient initialized for program: {program_id}")
    
    def _validate_configuration(self) -> None:
        """Validate client configuration."""
        if not self.api_token:
            raise ValueError("Bugcrowd API token is required")
        if not self.program_id:
            raise ValueError("Bugcrowd program ID is required")
        
        # Check ToS acceptance for bug bounty operations
        if not self.auth_service.check_tos_accepted():
            logger.warning("ToS not accepted for bug bounty operations")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request to Bugcrowd."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                data=data,
                json=json_data,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Log API call for audit purposes
            self._log_api_call(method, endpoint, response.status_code)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Bugcrowd API request failed: {e}")
            raise Exception(f"Bugcrowd API error: {str(e)}") from e
    
    def _log_api_call(self, method: str, endpoint: str, status_code: int) -> None:
        """Log API call for audit trail."""
        # In production, this would use proper logging to file/database
        logger.info(f"Bugcrowd API: {method} {endpoint} -> {status_code}")
    
    def get_program_details(self) -> Dict[str, Any]:
        """Get program details."""
        endpoint = f"programs/{self.program_id}"
        return self._make_request("GET", endpoint)
    
    def list_submissions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List vulnerability submissions."""
        endpoint = f"programs/{self.program_id}/submissions"
        params = {}
        if status:
            params["state"] = status
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("submissions", [])
    
    def create_submission(
        self,
        title: str,
        description: str,
        severity: str,
        steps_to_reproduce: str,
        vulnerability_type: str,
        impact: str,
        cvss_score: Optional[float] = None,
        references: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new vulnerability submission."""
        endpoint = f"programs/{self.program_id}/submissions"
        
        submission_data = {
            "submission": {
                "title": title,
                "description": description,
                "severity": severity,
                "steps_to_reproduce": steps_to_reproduce,
                "vulnerability_type": vulnerability_type,
                "impact": impact,
            }
        }
        
        if cvss_score:
            submission_data["submission"]["cvss_score"] = cvss_score
        
        if references:
            submission_data["submission"]["references"] = references
        
        return self._make_request("POST", endpoint, json_data=submission_data)
    
    def get_submission(self, submission_id: str) -> Dict[str, Any]:
        """Get specific submission details."""
        endpoint = f"submissions/{submission_id}"
        return self._make_request("GET", endpoint)
    
    def update_submission_status(self, submission_id: str, status: str) -> Dict[str, Any]:
        """Update submission status."""
        endpoint = f"submissions/{submission_id}"
        data = {
            "submission": {
                "state": status
            }
        }
        return self._make_request("PATCH", endpoint, json_data=data)
    
    def add_comment(self, submission_id: str, message: str) -> Dict[str, Any]:
        """Add comment to submission."""
        endpoint = f"submissions/{submission_id}/comments"
        data = {
            "comment": {
                "message": message
            }
        }
        return self._make_request("POST", endpoint, json_data=data)
    
    def upload_attachment(self, submission_id: str, file_path: str, description: str) -> Dict[str, Any]:
        """Upload attachment to submission."""
        endpoint = f"submissions/{submission_id}/attachments"
        
        with open(file_path, 'rb') as file:
            files = {
                'file': (file_path, file)
            }
            data = {
                'attachment': json.dumps({
                    'description': description
                })
            }
            
            return self._make_request("POST", endpoint, files=files, data=data)
    
    def get_bounty_info(self, submission_id: str) -> Dict[str, Any]:
        """Get bounty information for a submission."""
        endpoint = f"submissions/{submission_id}/bounty"
        return self._make_request("GET", endpoint)
    
    def search_programs(self, query: str) -> List[Dict[str, Any]]:
        """Search for Bugcrowd programs."""
        endpoint = "programs"
        params = {"q": query}
        response = self._make_request("GET", endpoint, params=params)
        return response.get("programs", [])
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get authenticated user profile."""
        endpoint = "user"
        return self._make_request("GET", endpoint)
    
    def validate_api_token(self) -> bool:
        """Validate API token."""
        try:
            self.get_user_profile()
            return True
        except Exception:
            return False
