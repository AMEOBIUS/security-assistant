"""
WAF Detection and Fingerprinting

Identifies Web Application Firewalls through:
- HTTP header analysis
- Error page fingerprinting
- Behavioral testing
- Response time analysis
"""

import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

from security_assistant.offensive.authorization import AuthorizationService

logger = logging.getLogger(__name__)


class WAFDetector:
    """
    WAF detection and fingerprinting engine.
    
    Args:
        timeout: Request timeout in seconds
        user_agent: Custom user agent for requests
        auth_service: Authorization service for ToS checking
    """
    
    # WAF signatures database
    WAF_SIGNATURES = {
        "Cloudflare": {
            "headers": ["cf-ray", "cf-request-id", "server: cloudflare"],
            "cookies": ["__cfduid", "__cf_bm"],
            "error_pages": ["cloudflare", "cf-ray"],
            "behavior": {"block_page": "Access Denied", "challenge": "Please complete the security check"}
        },
        "AWS WAF": {
            "headers": ["x-amz-cf-id", "x-amzn-requestid"],
            "error_pages": ["AWS WAF", "Request blocked"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        },
        "ModSecurity": {
            "headers": ["x-modsecurity-action", "x-modsecurity-rule"],
            "error_pages": ["mod_security", "ModSecurity Action"],
            "behavior": {"block_page": "ModSecurity Action", "status_code": 406}
        },
        "Imperva": {
            "headers": ["x-iinfo", "x-cdn"],
            "cookies": ["incap_ses_"],
            "error_pages": ["Imperva", "incap_ses"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        },
        "Akamai": {
            "headers": ["x-akamai-request-id", "x-akamai-session-info"],
            "error_pages": ["Akamai", "Reference #"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        },
        "Sucuri": {
            "headers": ["x-sucuri-id", "x-sucuri-cache"],
            "error_pages": ["Sucuri", "sucuri.net"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        },
        "Barracuda": {
            "headers": ["x-barracuda"],
            "error_pages": ["barracuda", "Barracuda"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        },
        "F5 BIG-IP": {
            "headers": ["x-cnection", "x-wa-info"],
            "cookies": ["bigipserver"],
            "error_pages": ["F5 BIG-IP", "The requested URL was rejected"],
            "behavior": {"block_page": "The requested URL was rejected", "status_code": 403}
        },
        "FortiWeb": {
            "headers": ["x-fortiweb"],
            "error_pages": ["FortiWeb", "fortinet"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        },
        "Palo Alto": {
            "headers": ["x-palo-alto"],
            "error_pages": ["Palo Alto", "paloaltonetworks"],
            "behavior": {"block_page": "Access Denied", "status_code": 403}
        }
    }
    
    def __init__(
        self,
        timeout: int = 30,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        auth_service: Optional[AuthorizationService] = None
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.auth_service = auth_service or AuthorizationService()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate"
        })
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info("WAFDetector initialized")
    
    def _validate_configuration(self) -> None:
        """Validate detector configuration."""
        if not self.auth_service.check_tos_accepted():
            logger.warning("ToS not accepted for WAF detection operations")
    
    def detect_waf(
        self,
        url: str,
        test_payloads: bool = False,
        max_tests: int = 3
    ) -> Dict[str, any]:
        """
        Detect WAF presence and type.
        
        Args:
            url: Target URL to test
            test_payloads: Whether to send test payloads for behavioral analysis
            max_tests: Maximum number of test payloads to send
            
        Returns:
            Detection results with WAF information
        """
        try:
            # Parse URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = f"https://{url}"
            
            # Step 1: Passive detection (headers, cookies)
            passive_results = self._passive_detection(url)
            
            if passive_results["detected"]:
                return passive_results
            
            # Step 2: Active detection (test payloads)
            if test_payloads:
                active_results = self._active_detection(url, max_tests)
                if active_results["detected"]:
                    return active_results
            
            # Step 3: Error page analysis
            error_results = self._error_page_analysis(url)
            if error_results["detected"]:
                return error_results
            
            return {
                "detected": False,
                "waf_type": "None",
                "confidence": "low",
                "evidence": [],
                "method": "comprehensive"
            }
            
        except Exception as e:
            logger.error(f"WAF detection failed: {e}")
            return {
                "detected": False,
                "waf_type": "None",
                "confidence": "low",
                "error": str(e),
                "method": "failed"
            }
    
    def _passive_detection(self, url: str) -> Dict[str, any]:
        """Passive WAF detection using headers and cookies."""
        try:
            # Make a normal request to analyze headers
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            detected_wafs = []
            
            # Check headers
            for waf_name, signatures in self.WAF_SIGNATURES.items():
                header_signatures = signatures.get("headers", [])
                for header in header_signatures:
                    if ":" in header:
                        header_name, header_value = header.split(":", 1)
                        if header_name.strip().lower() in response.headers:
                            if header_value.strip().lower() in response.headers[header_name.strip().lower()].lower():
                                detected_wafs.append({
                                    "waf": waf_name,
                                    "evidence": f"Header: {header_name}",
                                    "source": "header"
                                })
                    else:
                        if header.lower() in response.headers:
                            detected_wafs.append({
                                "waf": waf_name,
                                "evidence": f"Header: {header}",
                                "source": "header"
                            })
            
            # Check cookies
            for waf_name, signatures in self.WAF_SIGNATURES.items():
                cookie_signatures = signatures.get("cookies", [])
                for cookie in cookie_signatures:
                    if any(cookie.lower() in c.name.lower() or cookie.lower() in c.value.lower() 
                          for c in response.cookies):
                        detected_wafs.append({
                            "waf": waf_name,
                            "evidence": f"Cookie: {cookie}",
                            "source": "cookie"
                        })
            
            if detected_wafs:
                # Group by WAF and count evidence
                waf_counts = {}
                for detection in detected_wafs:
                    waf_counts[detection["waf"]] = waf_counts.get(detection["waf"], 0) + 1
                
                # Determine most likely WAF
                most_likely = max(waf_counts.items(), key=lambda x: x[1])
                confidence = "high" if most_likely[1] >= 2 else "medium"
                
                return {
                    "detected": True,
                    "waf_type": most_likely[0],
                    "confidence": confidence,
                    "evidence": detected_wafs,
                    "method": "passive"
                }
            
            return {"detected": False, "waf_type": "None", "confidence": "low", "evidence": []}
            
        except Exception as e:
            logger.warning(f"Passive detection failed: {e}")
            return {"detected": False, "waf_type": "None", "confidence": "low", "error": str(e)}
    
    def _active_detection(self, url: str, max_tests: int = 3) -> Dict[str, any]:
        """Active WAF detection using test payloads."""
        # Common WAF test payloads
        test_payloads = [
            {"payload": "' OR '1'='1", "type": "sqli", "expected": 500},
            {"payload": "<script>alert(1)</script>", "type": "xss", "expected": 403},
            {"payload": "../../../etc/passwd", "type": "lfi", "expected": 403},
            {"payload": "<?php echo 'test'; ?>", "type": "rce", "expected": 403}
        ]
        
        results = []
        
        for i, payload_data in enumerate(test_payloads[:max_tests]):
            try:
                # Add payload to URL parameter
                test_url = f"{url}?test={payload_data['payload']}" if "?" not in url else f"{url}&test={payload_data['payload']}"
                
                response = self.session.get(test_url, timeout=self.timeout, allow_redirects=False)
                
                # Check for WAF-like blocking behavior
                if response.status_code in [403, 406, 418, 500]:
                    # Check response content for WAF signatures
                    content = response.text.lower()
                    
                    for waf_name, signatures in self.WAF_SIGNATURES.items():
                        behavior = signatures.get("behavior", {})
                        if behavior.get("block_page", "").lower() in content:
                            results.append({
                                "waf": waf_name,
                                "evidence": f"Blocked {payload_data['type']} payload",
                                "payload": payload_data['payload'],
                                "status_code": response.status_code,
                                "source": "behavioral"
                            })
                        
                        # Check for generic WAF patterns
                        if any(keyword in content for keyword in ["access denied", "request blocked", "security check", "firewall"]):
                            results.append({
                                "waf": "Generic WAF",
                                "evidence": f"Blocked {payload_data['type']} payload",
                                "payload": payload_data['payload'],
                                "status_code": response.status_code,
                                "source": "behavioral"
                            })
                
            except Exception as e:
                logger.warning(f"Test payload {i+1} failed: {e}")
                continue
        
        if results:
            # Group by WAF and count evidence
            waf_counts = {}
            for detection in results:
                waf_counts[detection["waf"]] = waf_counts.get(detection["waf"], 0) + 1
            
            # Determine most likely WAF
            most_likely = max(waf_counts.items(), key=lambda x: x[1])
            confidence = "high" if most_likely[1] >= 2 else "medium"
            
            return {
                "detected": True,
                "waf_type": most_likely[0],
                "confidence": confidence,
                "evidence": results,
                "method": "active"
            }
        
        return {"detected": False, "waf_type": "None", "confidence": "low", "evidence": []}
    
    def _error_page_analysis(self, url: str) -> Dict[str, any]:
        """Analyze error pages for WAF signatures."""
        try:
            # Try to trigger an error page
            test_url = f"{url}/nonexistent-page-12345" if not url.endswith('/') else f"{url}nonexistent-page-12345"
            response = self.session.get(test_url, timeout=self.timeout, allow_redirects=False)
            
            if response.status_code == 404:
                content = response.text.lower()
                
                for waf_name, signatures in self.WAF_SIGNATURES.items():
                    error_pages = signatures.get("error_pages", [])
                    for error_page in error_pages:
                        if error_page.lower() in content:
                            return {
                                "detected": True,
                                "waf_type": waf_name,
                                "confidence": "medium",
                                "evidence": [{"waf": waf_name, "evidence": f"Error page: {error_page}", "source": "error_page"}],
                                "method": "error_analysis"
                            }
            
            return {"detected": False, "waf_type": "None", "confidence": "low"}
            
        except Exception as e:
            logger.warning(f"Error page analysis failed: {e}")
            return {"detected": False, "waf_type": "None", "confidence": "low", "error": str(e)}
    
    def detect_waf_batch(self, urls: List[str]) -> List[Dict[str, any]]:
        """Detect WAFs for multiple URLs."""
        results = []
        for url in urls:
            result = self.detect_waf(url)
            result["url"] = url
            results.append(result)
        return results
    
    def get_waf_signatures(self) -> Dict[str, any]:
        """Get all WAF signatures."""
        return self.WAF_SIGNATURES
    
    def validate_target(self, url: str) -> bool:
        """Validate target URL."""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except Exception:
            return False
