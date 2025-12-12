"""
Payload Obfuscation Engine

Advanced payload obfuscation techniques:
- Multi-layer encoding
- Context-aware obfuscation
- Randomized patterns
- Anti-analysis techniques
"""

import base64
import logging
import random
from typing import Dict, Optional

from security_assistant.offensive.authorization import AuthorizationService

logger = logging.getLogger(__name__)


class PayloadObfuscator:
    """
    Advanced payload obfuscation engine.
    
    Args:
        auth_service: Authorization service for ToS checking
    """
    
    def __init__(self, auth_service: Optional[AuthorizationService] = None):
        self.auth_service = auth_service or AuthorizationService()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info("PayloadObfuscator initialized")
    
    def _validate_configuration(self) -> None:
        """Validate obfuscator configuration."""
        if not self.auth_service.check_tos_accepted():
            logger.warning("ToS not accepted for payload obfuscation operations")
    
    def obfuscate(
        self,
        payload: str,
        layers: int = 3,
        context: Optional[str] = None
    ) -> str:
        """
        Obfuscate payload with multiple layers.
        
        Args:
            payload: Original payload
            layers: Number of obfuscation layers
            context: Context for context-aware obfuscation
            
        Returns:
            Obfuscated payload
        """
        obfuscated = payload
        
        for i in range(layers):
            technique = self._choose_technique(i, context)
            obfuscated = self._apply_obfuscation(obfuscated, technique)
        
        return obfuscated
    
    def _choose_technique(self, layer: int, context: Optional[str]) -> str:
        """Choose obfuscation technique based on layer and context."""
        techniques = ["base64", "hex", "url", "unicode", "javascript", "reverse", "shuffle"]
        
        if context == "sqli":
            techniques.extend(["sql_comment", "sql_case", "sql_concat"])
        elif context == "xss":
            techniques.extend(["html_entity", "js_escape", "css_obfuscate"])
        elif context == "lfi":
            techniques.extend(["path_obfuscate", "null_byte", "encoding"])
        
        return random.choice(techniques)
    
    def _apply_obfuscation(self, payload: str, technique: str) -> str:
        """Apply specific obfuscation technique."""
        try:
            if technique == "base64":
                return self._base64_obfuscate(payload)
            elif technique == "hex":
                return self._hex_obfuscate(payload)
            elif technique == "url":
                return self._url_obfuscate(payload)
            elif technique == "unicode":
                return self._unicode_obfuscate(payload)
            elif technique == "javascript":
                return self._javascript_obfuscate(payload)
            elif technique == "reverse":
                return self._reverse_obfuscate(payload)
            elif technique == "shuffle":
                return self._shuffle_obfuscate(payload)
            elif technique == "sql_comment":
                return self._sql_comment_obfuscate(payload)
            elif technique == "sql_case":
                return self._sql_case_obfuscate(payload)
            elif technique == "sql_concat":
                return self._sql_concat_obfuscate(payload)
            elif technique == "html_entity":
                return self._html_entity_obfuscate(payload)
            elif technique == "js_escape":
                return self._js_escape_obfuscate(payload)
            elif technique == "css_obfuscate":
                return self._css_obfuscate(payload)
            elif technique == "path_obfuscate":
                return self._path_obfuscate(payload)
            elif technique == "null_byte":
                return self._null_byte_obfuscate(payload)
            elif technique == "encoding":
                return self._encoding_obfuscate(payload)
            else:
                return payload
        except Exception as e:
            logger.error(f"Obfuscation technique {technique} failed: {e}")
            return payload
    
    def _base64_obfuscate(self, payload: str) -> str:
        """Base64 obfuscation."""
        import base64
        return base64.b64encode(payload.encode()).decode()
    
    def _hex_obfuscate(self, payload: str) -> str:
        """Hex obfuscation."""
        return payload.encode('utf-8').hex()
    
    def _url_obfuscate(self, payload: str) -> str:
        """URL obfuscation."""
        from urllib.parse import quote
        return quote(payload)
    
    def _unicode_obfuscate(self, payload: str) -> str:
        """Unicode obfuscation."""
        return ''.join(f'\\u{ord(c):04x}' for c in payload)
    
    def _javascript_obfuscate(self, payload: str) -> str:
        """JavaScript obfuscation."""
        return f"String.fromCharCode({','.join(str(ord(c)) for c in payload)})"
    
    def _reverse_obfuscate(self, payload: str) -> str:
        """Reverse string obfuscation."""
        return payload[::-1]
    
    def _shuffle_obfuscate(self, payload: str) -> str:
        """Shuffle characters obfuscation."""
        chars = list(payload)
        random.shuffle(chars)
        return ''.join(chars)
    
    def _sql_comment_obfuscate(self, payload: str) -> str:
        """SQL comment obfuscation."""
        return payload.replace(' ', '/**/')
    
    def _sql_case_obfuscate(self, payload: str) -> str:
        """SQL case variation obfuscation."""
        return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in payload)
    
    def _sql_concat_obfuscate(self, payload: str) -> str:
        """SQL concatenation obfuscation."""
        return payload.replace(' ', '||')
    
    def _html_entity_obfuscate(self, payload: str) -> str:
        """HTML entity obfuscation."""
        return ''.join(f'&#{ord(c)};' for c in payload)
    
    def _js_escape_obfuscate(self, payload: str) -> str:
        """JavaScript escape obfuscation."""
        return payload.encode('unicode-escape').decode()
    
    def _css_obfuscate(self, payload: str) -> str:
        """CSS obfuscation."""
        return payload.replace(' ', '\20')
    
    def _path_obfuscate(self, payload: str) -> str:
        """Path obfuscation."""
        return payload.replace('/', '/./')
    
    def _null_byte_obfuscate(self, payload: str) -> str:
        """Null byte obfuscation."""
        return payload + '\x00'
    
    def _encoding_obfuscate(self, payload: str) -> str:
        """Multi-encoding obfuscation."""
        return base64.b64encode(base64.b64encode(payload.encode())).decode()
    
    def generate_obfuscation_strategy(
        self,
        payload_type: str,
        waf_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate optimal obfuscation strategy.
        
        Args:
            payload_type: Type of payload (sqli, xss, lfi, etc.)
            waf_type: Detected WAF type (optional)
            
        Returns:
            Obfuscation strategy
        """
        strategy = {
            "payload_type": payload_type,
            "waf_type": waf_type or "unknown",
            "recommended_techniques": [],
            "layers": 3,
            "success_rate": "medium"
        }
        
        # Payload type specific strategies
        if payload_type == "sqli":
            strategy["recommended_techniques"] = ["sql_comment", "sql_case", "base64"]
            strategy["layers"] = 4
            strategy["success_rate"] = "high"
        elif payload_type == "xss":
            strategy["recommended_techniques"] = ["html_entity", "javascript", "unicode"]
            strategy["layers"] = 5
            strategy["success_rate"] = "high"
        elif payload_type == "lfi":
            strategy["recommended_techniques"] = ["path_obfuscate", "null_byte", "hex"]
            strategy["layers"] = 3
            strategy["success_rate"] = "medium"
        
        # WAF-specific adjustments
        if waf_type == "Cloudflare":
            strategy["recommended_techniques"].extend(["base64", "javascript"])
        elif waf_type == "ModSecurity":
            strategy["recommended_techniques"].extend(["unicode", "reverse"])
        
        return strategy
