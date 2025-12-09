"""
Safety Checker for Auto-PoC Generation.

Ensures that generated Proof-of-Concept code does not contain:
- Destructive commands (deletion, shutdown)
- Dangerous system interactions without warnings
- Malicious payloads that could harm the scanner host
"""

import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)


class PoCSafetyError(Exception):
    """Raised when generated PoC violates safety rules."""
    pass


class SafetyChecker:
    """
    Validates generated PoC code against safety rules.
    """

    # Regex patterns for dangerous operations
    DANGEROUS_PATTERNS = [
        (r"rm\s+-[rf]+", "File deletion command detected"),
        (r"del\s+[\/\\]", "File deletion command detected"),
        (r"DROP\s+TABLE", "Database drop command detected"),
        (r"shutdown", "System shutdown command detected"),
        (r":(){:|:&};:", "Fork bomb detected"),
        (r"mkfs", "Disk formatting command detected"),
        (r"dd\s+if=", "Disk write command detected"),
        (r"wget\s+http", "External download detected (potential malware dropper)"),
        (r"curl\s+http", "External download detected (potential malware dropper)"),
    ]

    # Patterns that require a warning but are allowed
    WARNING_PATTERNS = [
        (r"os\.system\(", "Uses os.system() - ensure input is sanitized"),
        (r"subprocess\.call\(", "Uses subprocess - ensure input is sanitized"),
        (r"eval\(", "Uses eval() - highly dangerous if running untrusted code"),
        (r"exec\(", "Uses exec() - highly dangerous"),
        (r"<script>", "Contains raw script tag - verify XSS payload context"),
    ]

    def validate(self, code: str) -> List[str]:
        """
        Validate code safety.
        
        Args:
            code: The source code to check
            
        Returns:
            List of warnings (empty if perfectly safe)
            
        Raises:
            PoCSafetyError: If a strictly forbidden pattern is found
        """
        warnings = []
        
        # Check forbidden patterns
        for pattern, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                logger.error(f"Safety violation: {reason}")
                raise PoCSafetyError(f"Safety violation: {reason}")

        # Check warnings
        for pattern, reason in self.WARNING_PATTERNS:
            if re.search(pattern, code):
                warnings.append(reason)
                
        return warnings

    def sanitize_payload(self, payload: str) -> str:
        """
        Sanitize a payload string (e.g. for injection).
        
        Removes obviously destructive parts while keeping the logic.
        """
        # Replace deletion commands with non-destructive equivalents
        payload = re.sub(r"rm\s+-[rf]+.*", "echo 'DELETED'", payload, flags=re.IGNORECASE)
        payload = re.sub(r"DROP\s+TABLE.*", "SELECT 1", payload, flags=re.IGNORECASE)
        
        return payload
