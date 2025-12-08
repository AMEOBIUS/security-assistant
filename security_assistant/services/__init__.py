"""
Services package for Security Assistant.

Provides modular services extracted from the monolithic orchestrator:
- DeduplicationService: Finding deduplication
- PriorityCalculator: Priority scoring (rule-based + ML)
- FindingConverter: Convert scanner findings to unified format
- MLScoringService: ML-based vulnerability scoring
- EnrichmentService: KEV, FP detection, reachability analysis
- ScanCoordinatorService: Parallel scanner execution
"""

from .deduplication import DeduplicationService, DeduplicationStrategy
from .enrichment_service import EnrichmentService, EnrichmentType
from .finding_converter import FindingConverter
from .issue_converter import IssueConverter
from .ml_scoring_service import MLScoringService
from .priority_calculator import PriorityCalculator
from .scan_coordinator_service import ScanCoordinatorService

__all__ = [
    "DeduplicationService",
    "DeduplicationStrategy",
    "PriorityCalculator",
    "FindingConverter",
    "MLScoringService",
    "EnrichmentService",
    "EnrichmentType",
    "ScanCoordinatorService",
    "IssueConverter",
]
