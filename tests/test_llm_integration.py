"""
Tests for LLM Integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding
from security_assistant.services.enrichment_service import EnrichmentService
from security_assistant.services.llm_service import LLMService
from security_assistant.services.priority_calculator import PriorityCalculator


@pytest.fixture
def mock_finding():
    return UnifiedFinding(
        finding_id="test-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="injection",
        file_path="app.py",
        line_start=10,
        line_end=10,
        title="SQL Injection",
        description="Possible SQL injection",
        code_snippet="cursor.execute(query)"
    )

@pytest.fixture
def mock_llm_service():
    service = MagicMock(spec=LLMService)
    service.calculate_priority = AsyncMock(return_value=85.0)
    service.detect_false_positive = AsyncMock(return_value=(True, "Test Reason"))
    return service

def test_priority_calculator_with_llm(mock_finding, mock_llm_service):
    """Test priority calculator uses LLM service."""
    calculator = PriorityCalculator(llm_service=mock_llm_service)
    
    score = calculator.calculate(mock_finding)
    
    assert score == 85.0
    mock_llm_service.calculate_priority.assert_called_once_with(mock_finding)

def test_enrichment_service_with_llm(mock_finding, mock_llm_service):
    """Test enrichment service uses LLM service for FP detection."""
    enrichment = EnrichmentService(
        enable_fp_detection=False, # Disable heuristic to focus on LLM
        llm_service=mock_llm_service
    )
    
    enrichment.detect_false_positives([mock_finding])
    
    assert mock_finding.is_false_positive is True
    assert "LLM: Test Reason" in mock_finding.fp_reasons
    mock_llm_service.detect_false_positive.assert_called_once_with(mock_finding)
