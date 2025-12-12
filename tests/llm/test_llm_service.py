"""Tests for LLM Service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from security_assistant.config import LLMConfig, LLMProvider, SecurityAssistantConfig
from security_assistant.llm import LLMResponse
from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding
from security_assistant.services.llm_service import LLMService


@pytest.fixture
def mock_config():
    config = MagicMock(spec=SecurityAssistantConfig)
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key="test-key",
        model="gpt-4"
    )
    config.llm = llm_config
    return config

@pytest.fixture
def mock_finding():
    return UnifiedFinding(
        finding_id="test-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="security",
        file_path="app.py",
        line_start=10,
        line_end=12,
        title="SQL Injection",
        description="Possible SQL injection vector",
        code_snippet="cursor.execute('SELECT * FROM users WHERE id=' + user_input)"
    )

@pytest.mark.asyncio
async def test_llm_service_initialization(mock_config):
    """Test service initialization with OpenAI provider."""
    service = LLMService(mock_config)
    assert service.client is not None
    assert service.config.provider == LLMProvider.OPENAI

@pytest.mark.asyncio
async def test_llm_service_disabled(mock_config):
    """Test service initialization when disabled."""
    mock_config.llm.provider = LLMProvider.DISABLED
    service = LLMService(mock_config)
    assert service.client is None

@pytest.mark.asyncio
async def test_explain_finding(mock_config, mock_finding):
    """Test explain_finding method."""
    service = LLMService(mock_config)
    
    # Mock client response
    mock_response = LLMResponse(content="This is an SQL injection.")
    service.client.complete = AsyncMock(return_value=mock_response)
    
    explanation = await service.explain_finding(mock_finding)
    
    assert explanation == "This is an SQL injection."
    service.client.complete.assert_called_once()
    
    # Check that prompt contains finding details
    call_args = service.client.complete.call_args
    prompt = call_args[0][0]
    assert "SQL Injection" in prompt
    assert "app.py" in prompt

@pytest.mark.asyncio
async def test_suggest_fix(mock_config, mock_finding):
    """Test suggest_fix method."""
    service = LLMService(mock_config)
    
    # Mock client response
    mock_response = LLMResponse(content="Use parameterized queries.")
    service.client.complete = AsyncMock(return_value=mock_response)
    
    fix = await service.suggest_fix(mock_finding)
    
    assert fix == "Use parameterized queries."
    
    # Check that prompt contains code snippet
    call_args = service.client.complete.call_args
    prompt = call_args[0][0]
    assert "cursor.execute" in prompt

@pytest.mark.asyncio
async def test_analyze_code(mock_config):
    """Test analyze_code method."""
    service = LLMService(mock_config)
    
    code = "def test(): pass"
    mock_response = LLMResponse(content='{"findings": []}')
    service.client.complete = AsyncMock(return_value=mock_response)
    
    result = await service.analyze_code(code, "test.py")
    
    assert result == '{"findings": []}'
    
    # Check prompt
    call_args = service.client.complete.call_args
    prompt = call_args[0][0]
    assert "def test(): pass" in prompt
