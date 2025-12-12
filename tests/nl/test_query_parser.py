"""Tests for Query Parser."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from security_assistant.llm import LLMResponse
from security_assistant.nl.query_parser import QueryParser, SearchIntent
from security_assistant.services.llm_service import LLMService


@pytest.fixture
def mock_llm_service():
    service = MagicMock(spec=LLMService)
    service.client = AsyncMock()
    service.is_available = AsyncMock(return_value=True)
    return service

@pytest.fixture
def parser(mock_llm_service):
    return QueryParser(mock_llm_service)

@pytest.mark.asyncio
async def test_parse_regex_find(parser):
    """Test heuristic parsing for find intent."""
    parser.llm_service.is_available.return_value = False
    query = "Find critical vulnerabilities"
    
    result = await parser.parse(query)
    
    assert result.intent == SearchIntent.FIND
    assert "CRITICAL" in result.filters.severity

@pytest.mark.asyncio
async def test_parse_regex_count(parser):
    """Test heuristic parsing for count intent."""
    parser.llm_service.is_available.return_value = False
    query = "Count high severity findings in app.py"
    
    result = await parser.parse(query)
    
    assert result.intent == SearchIntent.COUNT
    assert "HIGH" in result.filters.severity
    assert "app.py" in result.filters.file_pattern

@pytest.mark.asyncio
async def test_parse_llm(parser):
    """Test parsing with LLM."""
    mock_json = """
    {
        "intent": "find",
        "filters": {
            "severity": ["CRITICAL"],
            "keyword": "SQL injection"
        }
    }
    """
    parser.llm_service.client.complete.return_value = LLMResponse(content=mock_json)
    
    query = "Show me critical SQL injections"
    result = await parser.parse(query)
    
    assert result.intent == SearchIntent.FIND
    assert "CRITICAL" in result.filters.severity
    assert result.filters.keyword == "SQL injection"
