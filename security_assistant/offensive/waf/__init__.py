"""
WAF Bypass Engine Module

Provides WAF detection and bypass capabilities:
- WAF fingerprinting
- Bypass techniques
- Payload obfuscation
- Evasion strategies
"""

from security_assistant.offensive.waf.bypass import WAFBypassEngine
from security_assistant.offensive.waf.ctf import CTFChallengeMode
from security_assistant.offensive.waf.detector import WAFDetector
from security_assistant.offensive.waf.obfuscator import PayloadObfuscator

__all__ = [
    "WAFDetector",
    "WAFBypassEngine",
    "PayloadObfuscator",
    "CTFChallengeMode"
]
