"""Tests for LLM Enhancer."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from security_assistant.llm import LLMResponse
from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding
from security_assistant.poc.enhancers.llm_enhancer import LLMEnhancer
from security_assistant.services.llm_service import LLMService


@pytest.fixture
def mock_llm_service():
    service = MagicMock(spec=LLMService)
    service.client = AsyncMock()
    service.is_available = AsyncMock(return_value=True)
    return service

@pytest.fixture
def enhancer(mock_llm_service):
    return LLMEnhancer(mock_llm_service)

@pytest.fixture
def finding():
    return UnifiedFinding(
        finding_id="test-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="security",
        file_path="app.py",
        line_start=10,
        line_end=12,
        title="SQL Injection",
        description="SQLi",
        code_snippet="cursor.execute('SELECT * FROM users WHERE id=' + id)"
    )

@pytest.mark.asyncio
async def test_enhance_success(enhancer, finding):
    """Test successful enhancement."""
    mock_json = """
    {
        "target_url": "http://api.com/users",
        "param_name": "id",
        "payload": "' OR 1=1 --",
        "method": "GET",
        "notes": "Classic SQLi"
    }
    """
    enhancer.llm_service.client.complete.return_value = LLMResponse(content=mock_json)
    
    context = await enhancer.enhance(finding)
    
    assert context.target_url == "http://api.com/users"
    assert context.param_name == "id"
    assert context.payload == "' OR 1=1 --"

@pytest.mark.asyncio
async def test_enhance_llm_failure(enhancer, finding):
    """Test fallback when LLM fails."""
    enhancer.llm_service.client.complete.side_effect = Exception("API Error")
    
    context = await enhancer.enhance(finding)
    
    # Should return default
    assert context.target_url == "http://localhost:8000"
    assert context.payload == "' OR 1=1 --"

@pytest.mark.asyncio
async def test_enhance_invalid_json(enhancer, finding):
    """Test handling of invalid JSON response."""
    enhancer.llm_service.client.complete.return_value = LLMResponse(content="Not JSON")
    
    context = await enhancer.enhance(finding)
    
    # Should return default
    assert context.target_url == "http://localhost:8000"
