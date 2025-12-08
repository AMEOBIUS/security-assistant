"""
Reachability Analyzer

Main entry point for reachability analysis.
Integrates import tracking and call graph analysis to determine finding reachability.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .import_tracker import ImportTracker

logger = logging.getLogger(__name__)

@dataclass
class ReachabilityResult:
    """Result of reachability analysis."""
    is_reachable: bool
    confidence: float # 0.0 - 1.0
    reason: str
    usage_locations: list[str]

class ReachabilityAnalyzer:
    """
    Analyzes security findings to determine if they are reachable.
    
    Currently focused on SCA findings (vulnerable dependencies).
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.import_tracker = ImportTracker()
        self.is_analyzed = False
        
    def _ensure_analyzed(self):
        """Run analysis if not already done."""
        if not self.is_analyzed:
            logger.info(f"Analyzing project structure at {self.project_root}...")
            self.import_tracker.scan_directory(self.project_root)
            self.is_analyzed = True
            
    def analyze_dependency(self, package_name: str) -> ReachabilityResult:
        """
        Analyze reachability of a vulnerable dependency.
        
        Args:
            package_name: Name of the vulnerable package (e.g., "requests")
            
        Returns:
            ReachabilityResult
        """
        self._ensure_analyzed()
        
        # 1. Import Check (Is it even imported?)
        is_imported = self.import_tracker.is_library_used(package_name)
        usage_locations = self.import_tracker.get_usage_locations(package_name)
        
        if not is_imported:
            return ReachabilityResult(
                is_reachable=False,
                confidence=0.9,
                reason="Library is installed but never imported in Python code.",
                usage_locations=[]
            )
            
        # 2. Usage Check (Future: Is vulnerable function called?)
        # For now, if imported, we assume reachable with medium confidence
        # Deeper analysis requires call graph (Phase 2 of Reachability)
        
        return ReachabilityResult(
            is_reachable=True,
            confidence=0.5, # Medium confidence because we don't know if vulnerable *function* is used
            reason="Library is imported by the application.",
            usage_locations=usage_locations
        )
