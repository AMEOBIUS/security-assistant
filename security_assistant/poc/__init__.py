"""
Auto-PoC Generation Module.

Generates Proof-of-Concept exploits for detected vulnerabilities to verify their impact.
"""

from .generator import PoCError, PoCGenerator

__all__ = ["PoCGenerator", "PoCError"]
