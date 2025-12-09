"""
Natural Language Query Parser.

Converts natural language text into structured search queries using LLM or heuristics.
"""

import logging
import json
import re
from typing import Dict, Any, Optional

from security_assistant.services.llm_service import LLMService
from security_assistant.nl.schema import StructuredQuery, SearchIntent, SearchFilters

logger = logging.getLogger(__name__)


class QueryParser:
    """
    Parses natural language into StructuredQuery.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def parse(self, query_text: str) -> StructuredQuery:
        """
        Parse natural language query.
        
        Args:
            query_text: User input string
            
        Returns:
            StructuredQuery object
        """
        # Try LLM first if available
        if await self.llm_service.is_available():
            try:
                return await self._parse_with_llm(query_text)
            except Exception as e:
                logger.warning(f"LLM parsing failed: {e}. Falling back to regex.")
        
        # Fallback to simple regex parsing
        return self._parse_with_regex(query_text)

    async def _parse_with_llm(self, query: str) -> StructuredQuery:
        """Use LLM to extract intent and filters."""
        prompt = f"""
You are a Security Assistant Query Parser.
Convert the user's natural language query into a structured JSON search object.

Schema:
{{
    "intent": "find" | "count" | "explain",
    "filters": {{
        "severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"] (optional),
        "category": ["security", "secret", "misconfig"] (optional),
        "scanner": ["bandit", "semgrep", "trivy"] (optional),
        "file_pattern": "filename or path" (optional),
        "keyword": "search term" (optional)
    }},
    "limit": int (default 10)
}}

Examples:
- "Show critical SQL injections" -> {{ "intent": "find", "filters": {{ "severity": ["CRITICAL"], "keyword": "SQL injection" }} }}
- "How many high severity issues in app.py?" -> {{ "intent": "count", "filters": {{ "severity": ["HIGH"], "file_pattern": "app.py" }} }}

Query: "{query}"
Output JSON:
"""
        
        response = await self.llm_service.client.complete(
            prompt, 
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        data = self._parse_json(response.content)
        
        return StructuredQuery(
            intent=data.get("intent", SearchIntent.FIND),
            filters=SearchFilters(**data.get("filters", {})),
            limit=data.get("limit", 10),
            raw_query=query
        )

    def _parse_with_regex(self, query: str) -> StructuredQuery:
        """Heuristic parsing for basic queries."""
        query_lower = query.lower()
        filters = SearchFilters()
        
        # Detect Intent
        intent = SearchIntent.FIND
        if "count" in query_lower or "how many" in query_lower:
            intent = SearchIntent.COUNT
        elif "explain" in query_lower or "what is" in query_lower:
            intent = SearchIntent.EXPLAIN

        # Detect Severity
        severities = []
        if "critical" in query_lower: severities.append("CRITICAL")
        if "high" in query_lower: severities.append("HIGH")
        if "medium" in query_lower: severities.append("MEDIUM")
        if "low" in query_lower: severities.append("LOW")
        if severities:
            filters.severity = severities

        # Detect Scanner
        scanners = []
        if "bandit" in query_lower: scanners.append("bandit")
        if "semgrep" in query_lower: scanners.append("semgrep")
        if "trivy" in query_lower: scanners.append("trivy")
        if scanners:
            filters.scanner = scanners

        # Detect File (simple heuristic: extensions)
        file_match = re.search(r'\b[\w\/._-]+\.(py|js|ts|go|java|html|json|yaml|yml|lock)\b', query)
        if file_match:
            filters.file_pattern = file_match.group(0)

        return StructuredQuery(
            intent=intent,
            filters=filters,
            raw_query=query
        )

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Robust JSON parsing."""
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from LLM")
            return {}
