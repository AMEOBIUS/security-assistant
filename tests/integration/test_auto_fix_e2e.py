"""
Integration tests for auto-fix end-to-end workflow.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from security_assistant.integrations.gitlab_mr_creator import GitLabMRCreator
from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding
from security_assistant.services.batch_fix_service import BatchFixService
from security_assistant.services.fix_generator import FixGenerator
from security_assistant.services.test_generator import PytestTestGenerator


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    service = Mock()
    service.client = Mock()
    service.client.complete = AsyncMock(return_value=Mock(
        content="""FIXED_CODE:
```python
# Fixed code
query = "SELECT * FROM users WHERE id=?"
cursor.execute(query, (user_id,))
```

EXPLANATION:
Used parameterized query to prevent SQL injection.
"""
    ))
    return service


@pytest.fixture
def sample_finding(tmp_path):
    """Sample finding with temp file."""
    test_file = tmp_path / "app.py"
    test_file.write_text('query = f"SELECT * FROM users WHERE id={user_id}"')
    
    return UnifiedFinding(
        finding_id="BANDIT-B201",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="SQL Injection",
        file_path=str(test_file),
        line_start=1,
        line_end=1,
        title="SQL Injection",
        description="User input in SQL query",
        code_snippet='query = f"SELECT * FROM users WHERE id={user_id}"'
    )


@pytest.mark.asyncio
async def test_single_fix_workflow(sample_finding, mock_llm_service):
    """Test complete single fix workflow."""
    # Initialize services
    fix_gen = FixGenerator(mock_llm_service)
    
    # Generate fix
    fixed_code, explanation = await fix_gen.generate_fix(sample_finding)
    
    # Verify
    assert "parameterized" in explanation.lower() or "?" in fixed_code
    assert fixed_code
    assert explanation


@pytest.mark.asyncio
async def test_batch_fix_workflow(sample_finding, mock_llm_service, tmp_path):
    """Test complete batch fix workflow."""
    # Create second finding
    test_file2 = tmp_path / "db.py"
    test_file2.write_text('query = f"UPDATE users SET name={name}"')
    
    finding2 = UnifiedFinding(
        finding_id="BANDIT-B202",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="SQL Injection",
        file_path=str(test_file2),
        line_start=1,
        line_end=1,
        title="SQL Injection #2",
        description="SQLi in update",
        code_snippet='query = f"UPDATE users SET name={name}"'
    )
    
    # Initialize services
    fix_gen = FixGenerator(mock_llm_service)
    test_gen = PytestTestGenerator(mock_llm_service)
    mr_creator = GitLabMRCreator()
    
    batch_service = BatchFixService(fix_gen, test_gen, mr_creator)
    
    # Batch fix
    result = await batch_service.batch_fix(
        [sample_finding, finding2],
        strategy="safe",
        generate_tests=False
    )
    
    # Verify
    assert result.success_count == 2
    assert result.failure_count == 0


@pytest.mark.asyncio  
async def test_fix_with_test_generation(sample_finding, mock_llm_service):
    """Test fix with test generation."""
    # Mock test generation
    mock_llm_service.client.complete = AsyncMock(side_effect=[
        # First call: fix generation
        Mock(content="""FIXED_CODE:
```python
query = "SELECT * FROM users WHERE id=?"
```

EXPLANATION:
Fixed SQLi
"""),
        # Second call: test generation
        Mock(content="""TEST_CODE:
```python
def test_query():
    assert "?" in query
```
""")
    ])
    
    fix_gen = FixGenerator(mock_llm_service)
    test_gen = PytestTestGenerator(mock_llm_service)
    
    # Generate fix
    fixed_code, explanation = await fix_gen.generate_fix(sample_finding)
    
    # Generate test
    test_code, test_path = await test_gen.generate_test(sample_finding, fixed_code)
    
    # Verify
    assert fixed_code
    assert test_code
    assert "test_" in test_path
    assert "def test_" in test_code
