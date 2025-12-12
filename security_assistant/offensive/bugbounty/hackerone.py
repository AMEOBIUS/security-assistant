"""
HackerOne API Client

Integration with HackerOne platform for:
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


class HackerOneClient:
    """
    HackerOne API client for bug bounty operations.
    
    Args:
        api_token: HackerOne API token
        program_handle: HackerOne program handle (e.g., "company")
        auth_service: Authorization service for ToS checking
    """
    
    BASE_URL = "https://api.hackerone.com/v1"
    
    def __init__(
        self,
        api_token: str,
        program_handle: str,
        auth_service: Optional[AuthorizationService] = None
    ):
        self.api_token = api_token
        self.program_handle = program_handle
        self.auth_service = auth_service or AuthorizationService()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"HackerOneClient initialized for program: {program_handle}")
    
    def _validate_configuration(self) -> None:
        """Validate client configuration."""
        if not self.api_token:
            raise ValueError("HackerOne API token is required")
        if not self.program_handle:
            raise ValueError("HackerOne program handle is required")
        
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
        """Make API request to HackerOne."""
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
            logger.error(f"HackerOne API request failed: {e}")
            raise Exception(f"HackerOne API error: {str(e)}") from e
    
    def _log_api_call(self, method: str, endpoint: str, status_code: int) -> None:
        """Log API call for audit trail."""
        # In production, this would use proper logging to file/database
        logger.info(f"HackerOne API: {method} {endpoint} -> {status_code}")
    
    def get_program_details(self) -> Dict[str, Any]:
        """Get program details."""
        endpoint = f"programs/{self.program_handle}"
        return self._make_request("GET", endpoint)
    
    def get_program_structure(self) -> Dict[str, Any]:
        """Get program structure and scope."""
        endpoint = f"programs/{self.program_handle}/structure"
        return self._make_request("GET", endpoint)
    
    def list_reports(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List vulnerability reports."""
        endpoint = f"programs/{self.program_handle}/reports"
        params = {}
        if status:
            params["status"] = status
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("data", [])
    
    def create_report(
        self,
        title: str,
        vulnerability_description: str,
        severity: str,
        steps_to_reproduce: str,
        attack_surface: str,
        impact: str,
        cvss_score: Optional[float] = None,
        references: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new vulnerability report."""
        endpoint = f"programs/{self.program_handle}/reports"
        
        report_data = {
            "data": {
                "type": "report",
                "attributes": {
                    "title": title,
                    "vulnerability_information": vulnerability_description,
                    "severity": severity,
                    "steps_to_reproduce": steps_to_reproduce,
                    "attack_surface": attack_surface,
                    "impact": impact,
                }
            }
        }
        
        if cvss_score:
            report_data["data"]["attributes"]["cvss_score"] = cvss_score
        
        if references:
            report_data["data"]["attributes"]["references"] = references
        
        return self._make_request("POST", endpoint, json_data=report_data)
    
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get specific report details."""
        endpoint = f"reports/{report_id}"
        return self._make_request("GET", endpoint)
    
    def update_report_status(self, report_id: str, status: str) -> Dict[str, Any]:
        """Update report status."""
        endpoint = f"reports/{report_id}"
        data = {
            "data": {
                "type": "report",
                "attributes": {
                    "state": status
                }
            }
        }
        return self._make_request("PATCH", endpoint, json_data=data)
    
    def add_comment(self, report_id: str, message: str) -> Dict[str, Any]:
        """Add comment to report."""
        endpoint = f"reports/{report_id}/activities"
        data = {
            "data": {
                "type": "activity",
                "attributes": {
                    "message": message,
                    "action": "comment"
                }
            }
        }
        return self._make_request("POST", endpoint, json_data=data)
    
    def upload_attachment(self, report_id: str, file_path: str, description: str) -> Dict[str, Any]:
        """Upload attachment to report."""
        endpoint = f"reports/{report_id}/attachments"
        
        with open(file_path, 'rb') as file:
            files = {
                'file': (file_path, file)
            }
            data = {
                'data': json.dumps({
                    'type': 'attachment',
                    'attributes': {
                        'description': description
                    }
                })
            }
            
            return self._make_request("POST", endpoint, files=files, data=data)
    
    def get_bounty_info(self, report_id: str) -> Dict[str, Any]:
        """Get bounty information for a report."""
        endpoint = f"reports/{report_id}/bounty"
        return self._make_request("GET", endpoint)
    
    def search_programs(self, query: str) -> List[Dict[str, Any]]:
        """Search for HackerOne programs."""
        endpoint = "programs"
        params = {"query": query}
        response = self._make_request("GET", endpoint, params=params)
        return response.get("data", [])
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get authenticated user profile."""
        endpoint = "users/me"
        return self._make_request("GET", endpoint)
    
    def validate_api_token(self) -> bool:
        """Validate API token."""
        try:
            self.get_user_profile()
            return True
        except Exception:
            return False
