"""
Tests for batch fix service.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding
from security_assistant.services.batch_fix_service import (
    BatchFixResult,
    BatchFixService,
)


@pytest.fixture
def sample_findings():
    """Sample findings for batch testing."""
    return [
        UnifiedFinding(
            finding_id="BANDIT-B201",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="SQL Injection",
            file_path="app.py",
            line_start=10,
            line_end=12,
            title="SQL Injection #1",
            description="SQLi in query",
            code_snippet='query = f"SELECT * FROM users WHERE id={user_id}"'
        ),
        UnifiedFinding(
            finding_id="BANDIT-B202",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="SQL Injection",
            file_path="db.py",
            line_start=20,
            line_end=22,
            title="SQL Injection #2",
            description="SQLi in update",
            code_snippet='query = f"UPDATE users SET name={name}"'
        )
    ]


@pytest.mark.asyncio
async def test_batch_fix_success(sample_findings):
    """Test successful batch fix."""
    # Mock services
    fix_gen = Mock()
    fix_gen.generate_fix = AsyncMock(return_value=("fixed code", "explanation"))
    
    test_gen = Mock()
    # Return different test paths for each finding
    test_gen.generate_test = AsyncMock(side_effect=[
        ("test code 1", "tests/test_app.py"),
        ("test code 2", "tests/test_db.py")
    ])
    
    mr_creator = Mock()
    
    service = BatchFixService(fix_gen, test_gen, mr_creator)
    
    # Batch fix
    result = await service.batch_fix(sample_findings, generate_tests=True)
    
    assert result.success_count == 2
    assert result.failure_count == 0
    assert len(result.generated_tests) == 2


@pytest.mark.asyncio
async def test_batch_fix_partial_failure(sample_findings):
    """Test batch fix with some failures."""
    # Mock services
    fix_gen = Mock()
    
    # First succeeds, second fails
    fix_gen.generate_fix = AsyncMock(
        side_effect=[
            ("fixed code", "explanation"),
            Exception("LLM error")
        ]
    )
    
    test_gen = Mock()
    mr_creator = Mock()
    
    service = BatchFixService(fix_gen, test_gen, mr_creator)
    
    # Batch fix
    result = await service.batch_fix(sample_findings, generate_tests=False)
    
    assert result.success_count == 1
    assert result.failure_count == 1


def test_batch_result():
    """Test BatchFixResult."""
    result = BatchFixResult()
    
    assert result.success_count == 0
    assert result.failure_count == 0
    assert result.total_count == 0
    
    # Add success
    finding = Mock()
    result.successful_fixes.append((finding, "code", "explanation"))
    
    assert result.success_count == 1
    assert result.total_count == 1
