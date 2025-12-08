"""
Safe Context Pattern Detector

Detects safe contexts where vulnerabilities are unlikely (logging, comments, etc).

Common patterns:
- Logging statements (logger.info, print)
- Comments and docstrings
- Error messages
- Debug output

Version: 1.0.0
"""

import re


class SafeContextPattern:
    """
    Detects safe contexts where code is unlikely to be vulnerable.
    
    Some contexts (logging, comments) may contain sensitive data patterns
    but are not actually exploitable vulnerabilities.
    
    Example:
        >>> detector = SafeContextPattern()
        >>> code = "logger.info(f'User {user_id} logged in')"
        >>> is_safe = detector.is_safe_context(code)
        >>> print(is_safe)  # True
    """
    
    # Logging patterns
    LOGGING_PATTERNS = [
        r"logger\.",            # logger.info, logger.debug
        r"logging\.",           # logging.info
        r"log\.",               # log.debug
        r"print\(",             # print()
        r"console\.log\(",      # console.log (JavaScript)
        r"console\.debug\(",    # console.debug
        r"console\.warn\(",     # console.warn
        r"console\.error\(",    # console.error
    ]
    
    # Comment patterns
    COMMENT_PATTERNS = [
        r"^\s*#",               # Python comment
        r"^\s*//",              # JavaScript/C++ comment
        r"^\s*/\*",             # Multi-line comment start
        r"^\s*\*",              # Multi-line comment middle
        r"^\s*\*/",             # Multi-line comment end
        r'"""',                 # Python docstring
        r"'''",                 # Python docstring
    ]
    
    # Error/debug patterns
    ERROR_PATTERNS = [
        r"raise ",              # raise Exception
        r"throw ",              # throw new Error
        r"assert ",             # assert condition
        r"\.error\(",           # logger.error
        r"\.warning\(",         # logger.warning
        r"\.debug\(",           # logger.debug
    ]
    
    def __init__(self):
        """Initialize safe context pattern detector."""
        # Compile regex patterns
        self._logging_patterns = [re.compile(p) for p in self.LOGGING_PATTERNS]
        self._comment_patterns = [re.compile(p) for p in self.COMMENT_PATTERNS]
        self._error_patterns = [re.compile(p) for p in self.ERROR_PATTERNS]
    
    def is_logging(self, code: str) -> bool:
        """
        Check if code is a logging statement.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code is logging, False otherwise
        
        Example:
            >>> detector = SafeContextPattern()
            >>> code = "logger.info('User logged in')"
            >>> detector.is_logging(code)  # True
        """
        for pattern in self._logging_patterns:
            if pattern.search(code):
                return True
        
        return False
    
    def is_comment(self, code: str) -> bool:
        """
        Check if code is a comment or docstring.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code is a comment, False otherwise
        
        Example:
            >>> detector = SafeContextPattern()
            >>> code = "# This is a comment"
            >>> detector.is_comment(code)  # True
        """
        for pattern in self._comment_patterns:
            if pattern.match(code):
                return True
        
        return False
    
    def is_error_handling(self, code: str) -> bool:
        """
        Check if code is error handling.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code is error handling, False otherwise
        
        Example:
            >>> detector = SafeContextPattern()
            >>> code = "raise ValueError('Invalid input')"
            >>> detector.is_error_handling(code)  # True
        """
        for pattern in self._error_patterns:
            if pattern.search(code):
                return True
        
        return False
    
    def is_safe_context(self, code: str) -> bool:
        """
        Check if code is in a safe context.
        
        Args:
            code: Code snippet to check
        
        Returns:
            True if code is in safe context, False otherwise
        
        Example:
            >>> detector = SafeContextPattern()
            >>> code = "logger.debug(f'SQL: {query}')"
            >>> detector.is_safe_context(code)  # True
        """
        return (
            self.is_logging(code) or
            self.is_comment(code) or
            self.is_error_handling(code)
        )
    
    def get_confidence(self, code: str) -> float:
        """
        Get confidence score (0.0-1.0) that code is in safe context.
        
        Args:
            code: Code snippet to check
        
        Returns:
            Confidence score (0.0 = not safe, 1.0 = definitely safe)
        
        Example:
            >>> detector = SafeContextPattern()
            >>> code = "# logger.info('Debug: ' + user_input)"
            >>> confidence = detector.get_confidence(code)
            >>> print(confidence)  # 1.0 (comment + logging)
        """
        score = 0.0
        
        # Logging (0.4 weight)
        if self.is_logging(code):
            score += 0.4
        
        # Comment (0.4 weight)
        if self.is_comment(code):
            score += 0.4
        
        # Error handling (0.2 weight)
        if self.is_error_handling(code):
            score += 0.2
        
        return min(score, 1.0)
