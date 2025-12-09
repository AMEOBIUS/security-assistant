"""Tests for PoC Generator."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from security_assistant.poc.generator import PoCGenerator, PoCError
from security_assistant.orchestrator import UnifiedFinding, ScannerType, FindingSeverity

@pytest.fixture
def generator():
    return PoCGenerator()

@pytest.fixture
def sqli_finding():
    return UnifiedFinding(
        finding_id="test-sqli-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="security",
        file_path="app.py",
        line_start=10,
        line_end=12,
        title="Possible SQL Injection",
        description="SQL injection detected",
        code_snippet="cursor.execute(query)"
    )

@pytest.fixture
def xss_finding():
    return UnifiedFinding(
        finding_id="test-xss-1",
        scanner=ScannerType.SEMGREP,
        severity=FindingSeverity.MEDIUM,
        category="security",
        file_path="templates/index.html",
        line_start=5,
        line_end=5,
        title="Reflected XSS",
        description="XSS detected in template",
        code_snippet="{{ user_input | safe }}"
    )

def test_template_selection_sqli(generator, sqli_finding):
    """Test SQLi template selection."""
    template = generator._get_template_name(sqli_finding)
    assert template == "sqli.py.j2"

def test_template_selection_xss(generator, xss_finding):
    """Test XSS template selection."""
    template = generator._get_template_name(xss_finding)
    assert template == "xss.html.j2"

@pytest.mark.asyncio
async def test_generate_sqli_poc(generator, sqli_finding):
    """Test generating SQLi PoC code."""
    poc_code = await generator.generate(sqli_finding)
    
    assert "import requests" in poc_code
    assert "Possible SQL Injection" in poc_code
    assert "test-sqli-1" in poc_code
    assert "test_sqli" in poc_code

@pytest.mark.asyncio
async def test_generate_xss_poc(generator, xss_finding):
    """Test generating XSS PoC code."""
    poc_code = await generator.generate(xss_finding)
    
    assert "<!DOCTYPE html>" in poc_code
    assert "XSS PoC" in poc_code
    assert "test-xss-1" in poc_code
    assert "<script>alert(1)</script>" in poc_code

@pytest.mark.asyncio
async def test_unknown_finding_type(generator):
    """Test handling of unknown finding types."""
    finding = UnifiedFinding(
        finding_id="test-unknown",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.LOW,
        category="security",
        file_path="test.py",
        line_start=1,
        line_end=1,
        title="Unknown Issue",
        description="Something weird",
        code_snippet="pass"
    )
    
    with pytest.raises(PoCError, match="No suitable PoC template"):
        await generator.generate(finding)
