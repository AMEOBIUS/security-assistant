"""Tests for Query Executor."""

import pytest

from security_assistant.nl.query_executor import QueryExecutor
from security_assistant.nl.schema import SearchFilters, SearchIntent, StructuredQuery


@pytest.fixture
def executor():
    return QueryExecutor()

@pytest.fixture
def findings():
    return [
        {
            "id": "1",
            "severity": "CRITICAL",
            "category": "security",
            "file": "app.py",
            "title": "SQL Injection"
        },
        {
            "id": "2",
            "severity": "HIGH",
            "category": "security",
            "file": "utils.py",
            "title": "XSS"
        },
        {
            "id": "3",
            "severity": "LOW",
            "category": "style",
            "file": "app.py",
            "title": "Line too long"
        }
    ]

def test_execute_find_critical(executor, findings):
    """Test finding critical issues."""
    query = StructuredQuery(
        intent=SearchIntent.FIND,
        filters=SearchFilters(severity=["CRITICAL"])
    )
    result = executor.execute(query, findings)
    
    assert result["count"] == 1
    assert result["results"][0]["id"] == "1"

def test_execute_count_file(executor, findings):
    """Test counting issues in a file."""
    query = StructuredQuery(
        intent=SearchIntent.COUNT,
        filters=SearchFilters(file_pattern="app.py")
    )
    result = executor.execute(query, findings)
    
    assert result["count"] == 2

def test_execute_keyword(executor, findings):
    """Test keyword search."""
    query = StructuredQuery(
        intent=SearchIntent.FIND,
        filters=SearchFilters(keyword="SQL")
    )
    result = executor.execute(query, findings)
    
    assert result["count"] == 1
    assert result["results"][0]["title"] == "SQL Injection"
