"""
Sanitization Pattern Detector

Detects code that sanitizes/validates input, reducing false positive risk.

Common patterns:
- escape(), html.escape(), urllib.parse.quote()
- validate(), sanitize(), clean()
- re.escape(), bleach.clean()
- Input validation (isinstance, type checks)

Version: 1.0.0
"""

import re
from typing import Optional


class SanitizationPattern:
    """
    Detects input sanitization patterns.
    
    Code that properly sanitizes input is less likely to be vulnerable,
    even if it uses potentially dangerous functions.
    
    Example:
        >>> detector = SanitizationPattern()
        >>> code = "safe_input = html.escape(user_input)"
        >>> is_sanitized = detector.is_sanitized(code)
        >>> print(is_sanitized)  # True
    """
    
    # Sanitization function patterns
    SANITIZATION_PATTERNS = [
        # HTML/XML escaping
        r"html\.escape\(",
        r"xml\.sax\.saxutils\.escape\(",
        r"cgi\.escape\(",
        r"bleach\.clean\(",
        r"markupsafe\.escape\(",
        
        # URL encoding
        r"urllib\.parse\.quote\(",
        r"urllib\.parse\.quote_plus\(",
        r"requests\.utils\.quote\(",
        
        # SQL escaping (though parameterized queries are better)
        r"pymysql\.escape_string\(",
        r"psycopg2\.extensions\.adapt\(",
        
        # Regex escaping
        r"re\.escape\(",
        
        # Generic sanitization
        r"sanitize\(",
        r"clean\(",
        r"validate\(",
        r"escape\(",
        r"filter\(",
        
        # Input validation
        r"isinstance\(",
        r"type\(",
        r"\.isdigit\(",
        r"\.isalpha\(",
        r"\.isalnum\(",
        
        # Whitelist patterns
        r"if .* in \[",          # if x in [allowed_values]
        r"if .* in \{",          # if x in {allowed_values}
        r"if .* == ['\"]",       # if x == "expected"
    ]
    
    # Validation keywords
    VALIDATION_KEYWORDS = [
        "validate",
        "sanitize",
        "clean",
        "escape",
        "filter",
        "whitelist",
        "allowed",
        "safe",
    ]
    
    def __init__(self):
        """Initialize sanitization pattern detector."""
        # Compile regex patterns
        self._patterns = [re.compile(p) for p in self.SANITIZATION_PATTERNS]
    
    def is_sanitized(self, code: str) -> bool:
        """
        Check if code contains sanitization patterns.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code contains sanitization, False otherwise
        
        Example:
            >>> detector = SanitizationPattern()
            >>> code = "safe = html.escape(user_input)"
            >>> detector.is_sanitized(code)  # True
        """
        for pattern in self._patterns:
            if pattern.search(code):
                return True
        
        return False
    
    def has_validation(self, code: str) -> bool:
        """
        Check if code contains validation keywords.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code contains validation keywords, False otherwise
        
        Example:
            >>> detector = SanitizationPattern()
            >>> code = "def validate_input(data): ..."
            >>> detector.has_validation(code)  # True
        """
        code_lower = code.lower()
        
        for keyword in self.VALIDATION_KEYWORDS:
            if keyword in code_lower:
                return True
        
        return False
    
    def get_confidence(self, code: str) -> float:
        """
        Get confidence score (0.0-1.0) that code is sanitized.
        
        Args:
            code: Code snippet to check
        
        Returns:
            Confidence score (0.0 = not sanitized, 1.0 = definitely sanitized)
        
        Example:
            >>> detector = SanitizationPattern()
            >>> code = "safe = html.escape(validate(user_input))"
            >>> confidence = detector.get_confidence(code)
            >>> print(confidence)  # 1.0 (high confidence)
        """
        score = 0.0
        
        # Sanitization function (0.7 weight)
        if self.is_sanitized(code):
            score += 0.7
        
        # Validation keywords (0.3 weight)
        if self.has_validation(code):
            score += 0.3
        
        return min(score, 1.0)
