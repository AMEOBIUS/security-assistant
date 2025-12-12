"""
Base Scanner Classes for Offensive Security

Base classes and data structures for offensive security scanners.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ScannerFinding:
    """
    Represents a single finding from an offensive security scanner.
    """
    
    scanner: str
    target: str
    port: Optional[int] = None
    protocol: Optional[str] = None
    severity: str = "INFO"
    description: str = ""
    solution: str = ""
    references: List[str] = None
    
    def __post_init__(self):
        if self.references is None:
            self.references = []


@dataclass
class ScannerResult:
    """
    Represents results from an offensive security scan.
    """
    
    scanner: str
    target: str
    findings: List[ScannerFinding]
    start_time: str
    end_time: str
    scan_type: str
    
    def __post_init__(self):
        if self.findings is None:
            self.findings = []
