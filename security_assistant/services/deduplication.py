"""
Deduplication Service for Security Findings.

Provides configurable strategies for deduplicating findings
from multiple scanners.
"""

import logging
from enum import Enum
from typing import List, Set

logger = logging.getLogger(__name__)


class DeduplicationStrategy(str, Enum):
    """Deduplication strategy options."""

    LOCATION = "location"  # Same file + line range
    CONTENT = "content"  # Same title + file + code hash
    BOTH = "both"  # Either location OR content match


class DeduplicationService:
    """
    Service for deduplicating security findings.

    Supports multiple strategies:
    - location: Deduplicate by file path and line numbers
    - content: Deduplicate by title, file, and code snippet hash
    - both: Combine both strategies

    Example:
        >>> service = DeduplicationService(strategy=DeduplicationStrategy.LOCATION)
        >>> unique_findings = service.deduplicate(all_findings)
    """

    def __init__(
        self, strategy: DeduplicationStrategy = DeduplicationStrategy.LOCATION
    ):
        """
        Initialize deduplication service.

        Args:
            strategy: Deduplication strategy to use
        """
        self.strategy = strategy
        logger.debug(
            f"DeduplicationService initialized with strategy: {strategy.value}"
        )

    def deduplicate(self, findings: List) -> List:
        """
        Deduplicate findings based on configured strategy.

        Args:
            findings: List of UnifiedFinding objects

        Returns:
            Deduplicated list of findings
        """
        if not findings:
            return findings

        seen_keys: Set[str] = set()
        deduplicated = []
        duplicates_count = 0

        for finding in findings:
            key = self._generate_key(finding)

            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(finding)
            else:
                duplicates_count += 1
                logger.debug(
                    f"Duplicate removed: {finding.title} at {finding.location_key}"
                )

        if duplicates_count > 0:
            logger.info(f"Deduplication removed {duplicates_count} duplicates")

        return deduplicated

    def _generate_key(self, finding) -> str:
        """Generate deduplication key based on strategy."""
        if self.strategy == DeduplicationStrategy.LOCATION:
            return finding.location_key
        elif self.strategy == DeduplicationStrategy.CONTENT:
            return finding.content_key
        else:  # BOTH
            return f"{finding.location_key}|{finding.content_key}"

    def get_duplicates_count(self, findings: List) -> int:
        """Count how many duplicates exist in findings list."""
        seen_keys: Set[str] = set()
        duplicates = 0

        for finding in findings:
            key = self._generate_key(finding)
            if key in seen_keys:
                duplicates += 1
            else:
                seen_keys.add(key)

        return duplicates
