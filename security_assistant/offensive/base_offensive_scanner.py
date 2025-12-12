"""
Base Offensive Scanner Class

Abstract base class for all offensive security scanners.

Features:
- Authorization enforcement
- ToS validation
- Audit logging
- Result standardization
- Safety checks

All offensive scanners must inherit from this class.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from security_assistant.offensive.authorization import (
    AuthorizationService,
)

logger = logging.getLogger(__name__)


class OffensiveScannerError(Exception):
    """Base exception for offensive scanner errors."""
    pass


class AuthorizationRequiredError(OffensiveScannerError):
    """Scanner requires authorization but ToS not accepted."""
    pass


class TargetNotAuthorizedError(OffensiveScannerError):
    """Target is not authorized for scanning."""
    pass


class OffensiveScanner(ABC):
    """
    Abstract base class for offensive security scanners.
    
    All offensive scanners must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, **kwargs):
        """Initialize offensive scanner."""
        self.auth_service = AuthorizationService()
        self._validate_tos_acceptance()
    
    def _validate_tos_acceptance(self):
        """Ensure ToS has been accepted before using offensive tools."""
        if not self.auth_service.check_tos_accepted():
            raise AuthorizationRequiredError(
                "Terms of Service must be accepted before using offensive tools. "
                "Run: security-assistant tos --accept"
            )
    
    def _check_authorization(self, target: str, target_type: Optional[str] = None):
        """
        Check if target is authorized for scanning.
        
        Args:
            target: Target to check
            target_type: Optional type hint
            
        Raises:
            TargetNotAuthorizedError: If target not authorized
            AuthorizationDatabaseError: If authorization check fails
        """
        if not self.auth_service.is_authorized(target, target_type):
            raise TargetNotAuthorizedError(
                f"Target not authorized: {target}. "
                f"Add with: security-assistant authorize --add {target}"
            )
        
        logger.info(f"Authorization confirmed for: {target}")
    
    @abstractmethod
    def scan(self, target: str, **kwargs) -> Any:
        """
        Perform offensive scan.
        
        Args:
            target: Target to scan
            **kwargs: Scanner-specific arguments
            
        Returns:
            Scanner-specific result
            
        Raises:
            TargetNotAuthorizedError: If target not authorized
            OffensiveScannerError: If scan fails
        """
        pass
    
    def _log_offensive_action(
        self,
        action: str,
        target: str,
        details: Optional[str] = None
    ):
        """
        Log offensive action to audit trail.
        
        Args:
            action: Action performed (scan, exploit, etc.)
            target: Target of action
            details: Additional details
        """
        try:
            # This will be enhanced with proper audit logging
            log_msg = f"[OFFENSIVE] {action}: {target}"
            if details:
                log_msg += f" Details: {details}"
            logger.info(log_msg)
        except Exception as e:
            logger.error(f"Failed to log offensive action: {e}")
    
    def _standardize_result(self, raw_result: Any) -> Dict:
        """
        Standardize scanner result format.
        
        Args:
            raw_result: Raw scanner output
            
        Returns:
            Standardized result dictionary
        """
        # Base implementation - subclasses should override
        return {
            "scanner": self.name,
            "target": getattr(self, '_current_target', 'unknown'),
            "status": "completed",
            "raw_result": raw_result,
            "timestamp": self._get_current_timestamp()
        }
    
    @property
    @abstractmethod
    def scanner_type(self) -> str:
        """Type of offensive scanner (e.g., 'network', 'web', 'database')."""
        pass
    
    @property
    @abstractmethod
    def risk_level(self) -> str:
        """Risk level of scanner (LOW, MEDIUM, HIGH, CRITICAL)."""
        pass
    
    def get_safety_recommendations(self) -> List[str]:
        """Get safety recommendations for this scanner."""
        return [
            "Always test in staging first",
            f"Review {self.scanner_type} scanner documentation",
            f"Consider {self.risk_level} risk level",
            "Monitor systems during scanning",
            "Have rollback plan ready"
        ]
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for logging."""
        from datetime import datetime
        return datetime.now().isoformat()


# Example usage:
# class MyOffensiveScanner(OffensiveScanner):
#     @property
#     def scanner_type(self) -> str:
#         return "network"
#     
#     @property
#     def risk_level(self) -> str:
#         return "MEDIUM"
#     
#     def scan(self, target: str, **kwargs) -> Dict:
#         self._check_authorization(target)
#         self._log_offensive_action("scan", target)
#         
#         # Perform scan...
#         result = {"vulnerabilities": []}
#         
#         return self._standardize_result(result)
