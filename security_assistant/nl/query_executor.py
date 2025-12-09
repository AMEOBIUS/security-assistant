"""
Query Executor.

Executes structured queries against scan results.
"""

import logging
from typing import Any, Dict, List

from security_assistant.nl.schema import SearchIntent, StructuredQuery

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes search queries on scan results."""

    def execute(self, query: StructuredQuery, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute query against a list of findings (dictionaries).
        
        Args:
            query: Parsed structured query
            findings: List of finding dictionaries (from scan-results.json)
            
        Returns:
            Result dictionary (e.g. {"count": 5} or {"results": [...]})
        """
        filtered = self._apply_filters(findings, query)
        
        if query.intent == SearchIntent.COUNT:
            return {
                "count": len(filtered),
                "query": query.raw_query,
                "filters": query.filters.model_dump(exclude_none=True)
            }
            
        elif query.intent == SearchIntent.FIND:
            limit = query.limit or 10
            return {
                "count": len(filtered),
                "results": filtered[:limit],
                "query": query.raw_query
            }
            
        else:
            return {"error": f"Unsupported intent: {query.intent}"}

    def _apply_filters(self, findings: List[Dict], query: StructuredQuery) -> List[Dict]:
        """Apply filters to findings list."""
        result = []
        
        f = query.filters
        
        for finding in findings:
            # Severity Filter
            if f.severity:
                # Normalize severity (some tools use CRITICAL, some Critical)
                sev = finding.get("severity", "").upper()
                if sev not in [s.upper() for s in f.severity]:
                    continue

            # Scanner Filter
            if f.scanner:
                scanner = finding.get("scanner", "").lower()
                if scanner not in [s.lower() for s in f.scanner]:
                    continue

            # Category Filter
            if f.category:
                cat = finding.get("category", "").lower()
                if not any(c.lower() in cat for c in f.category):
                    continue

            # File Pattern
            if f.file_pattern:
                path = finding.get("file", finding.get("file_path", ""))
                if f.file_pattern not in path:
                    continue

            # Keyword Search (Title, Description, Code)
            if f.keyword:
                kw = f.keyword.lower()
                text_content = (
                    finding.get("title", "") + " " + 
                    finding.get("description", "") + " " + 
                    finding.get("code_snippet", "")
                ).lower()
                if kw not in text_content:
                    continue

            result.append(finding)
            
        return result
