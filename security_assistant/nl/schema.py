"""
Data models for Natural Language Queries.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SearchIntent(str, Enum):
    """User intent classification."""
    FIND = "find"        # Find/List specific findings
    COUNT = "count"      # Count statistics
    EXPLAIN = "explain"  # Explain concepts or findings
    UNKNOWN = "unknown"  # Unclear intent

class SearchFilters(BaseModel):
    """Structured filters extracted from NL query."""
    severity: Optional[List[str]] = Field(None, description="Critical, High, Medium, Low")
    category: Optional[List[str]] = Field(None, description="Security, Secret, Misconfig")
    file_pattern: Optional[str] = Field(None, description="Glob pattern or filename")
    scanner: Optional[List[str]] = Field(None, description="Bandit, Semgrep, Trivy")
    cwe: Optional[List[str]] = Field(None, description="CWE IDs")
    keyword: Optional[str] = Field(None, description="Free text search keyword")

class StructuredQuery(BaseModel):
    """Parsed query ready for execution."""
    intent: SearchIntent
    filters: SearchFilters = Field(default_factory=SearchFilters)
    limit: Optional[int] = Field(10, description="Max results to return")
    raw_query: str = ""
