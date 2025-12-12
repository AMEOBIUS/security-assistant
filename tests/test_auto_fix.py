"""
Tests for auto-fix feature.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from security_assistant.integrations.gitlab_mr_creator import GitLabMRCreator
from security_assistant.orchestrator import FindingSeverity, ScannerType, UnifiedFinding
from security_assistant.services.fix_generator import FixGenerator, FixStrategy


@pytest.fixture
def sample_finding():
    """Sample security finding for testing."""
    return UnifiedFinding(
        finding_id="BANDIT-B201",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="SQL Injection",
        file_path="test_app.py",
        line_start=10,
        line_end=12,
        title="SQL Injection via string formatting",
        description="User input directly in SQL query",
        code_snippet='query = f"SELECT * FROM users WHERE id={user_id}"'
    )


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    service = Mock()
    service.client = Mock()
    service.client.complete = AsyncMock(return_value=Mock(
        content="""FIXED_CODE:
```python
# Fixed SQL injection vulnerability
query = "SELECT * FROM users WHERE id=?"
cursor.execute(query, (user_id,))
```

EXPLANATION:
Replaced string formatting with parameterized query to prevent SQL injection attacks.
"""
    ))
    return service


@pytest.mark.asyncio
async def test_fix_generator_basic(sample_finding, mock_llm_service, tmp_path):
    """Test basic fix generation."""
    # Create test file
    test_file = tmp_path / "test_app.py"
    test_file.write_text('query = f"SELECT * FROM users WHERE id={user_id}"')
    
    # Update finding path
    sample_finding.file_path = str(test_file)
    
    # Generate fix
    generator = FixGenerator(mock_llm_service)
    fixed_code, explanation = await generator.generate_fix(sample_finding)
    
    # Verify
    assert "parameterized" in explanation.lower()
    assert "?" in fixed_code
    assert "cursor.execute" in fixed_code


@pytest.mark.asyncio
async def test_fix_generator_strategies(sample_finding, mock_llm_service, tmp_path):
    """Test different fix strategies."""
    test_file = tmp_path / "test_app.py"
    test_file.write_text('query = f"SELECT * FROM users WHERE id={user_id}"')
    sample_finding.file_path = str(test_file)
    
    generator = FixGenerator(mock_llm_service)
    
    # Test each strategy
    for strategy in [FixStrategy.SAFE, FixStrategy.AGGRESSIVE, FixStrategy.MINIMAL]:
        fixed_code, explanation = await generator.generate_fix(sample_finding, strategy)
        assert fixed_code
        assert explanation
        
        # Verify strategy was passed to LLM
        call_args = mock_llm_service.client.complete.call_args
        assert strategy in call_args[0][0]  # Check prompt contains strategy


@pytest.mark.asyncio
async def test_fix_generator_file_not_found(sample_finding, mock_llm_service):
    """Test error handling for missing file."""
    sample_finding.file_path = "nonexistent.py"
    
    generator = FixGenerator(mock_llm_service)
    
    with pytest.raises(FileNotFoundError):
        await generator.generate_fix(sample_finding)


@pytest.mark.asyncio
async def test_fix_generator_invalid_response(sample_finding, mock_llm_service, tmp_path):
    """Test error handling for invalid LLM response."""
    test_file = tmp_path / "test_app.py"
    test_file.write_text('query = f"SELECT * FROM users WHERE id={user_id}"')
    sample_finding.file_path = str(test_file)
    
    # Mock invalid response
    mock_llm_service.client.complete = AsyncMock(return_value=Mock(
        content="Invalid response without markers"
    ))
    
    generator = FixGenerator(mock_llm_service)
    
    with pytest.raises(ValueError, match="Invalid LLM response format"):
        await generator.generate_fix(sample_finding)


def test_mr_creator_dry_run(sample_finding):
    """Test MR creation in dry-run mode."""
    creator = GitLabMRCreator()
    
    # Should not raise
    import asyncio
    result = asyncio.run(creator.create_fix_mr(
        sample_finding,
        "fixed code",
        "explanation",
        dry_run=True
    ))
    
    assert result is None  # Dry run returns None


@patch('subprocess.run')
def test_mr_creator_detect_project_id(mock_run):
    """Test GitLab project ID detection."""
    mock_run.return_value = Mock(
        stdout="https://gitlab.com/namespace/project.git\n",
        returncode=0
    )
    
    creator = GitLabMRCreator()
    
    assert creator.project_id == "namespace/project"


@patch('subprocess.run')
def test_mr_creator_commit_message(mock_run, sample_finding):
    """Test commit message generation."""
    creator = GitLabMRCreator()
    
    msg = creator._generate_commit_message(sample_finding, "Fixed SQL injection")
    
    assert "fix:" in msg
    assert sample_finding.title in msg
    assert sample_finding.severity.value in msg
    assert sample_finding.finding_id in msg
    assert "Fixed SQL injection" in msg


@patch('subprocess.run')
def test_mr_creator_mr_description(mock_run, sample_finding):
    """Test MR description generation."""
    creator = GitLabMRCreator()
    
    desc = creator._generate_mr_description(sample_finding, "Fixed SQL injection")
    
    assert sample_finding.title in desc
    assert sample_finding.severity.value in desc
    assert sample_finding.category in desc
    assert "Fixed SQL injection" in desc
    assert "Checklist" in desc
    assert sample_finding.finding_id in desc


@pytest.mark.asyncio
@patch('subprocess.run')
async def test_mr_creator_full_flow(mock_run, sample_finding, tmp_path):
    """Test full MR creation flow."""
    # Setup mocks
    mock_run.return_value = Mock(
        stdout="https://gitlab.com/namespace/project/-/merge_requests/1\n",
        returncode=0
    )
    
    # Create test file
    test_file = tmp_path / "test_app.py"
    test_file.write_text('original code')
    sample_finding.file_path = str(test_file)
    
    creator = GitLabMRCreator()
    
    # Create MR
    mr_url = await creator.create_fix_mr(
        sample_finding,
        "fixed code",
        "explanation",
        dry_run=False
    )
    
    # Verify git commands were called
    assert mock_run.call_count >= 4  # checkout, add, commit, push, glab
    
    # Verify file was updated
    assert test_file.read_text() == "fixed code"
    
    # Verify MR URL returned
    assert "merge_requests" in mr_url


def test_fix_strategy_values():
    """Test FixStrategy enum values."""
    assert FixStrategy.SAFE == "safe"
    assert FixStrategy.AGGRESSIVE == "aggressive"
    assert FixStrategy.MINIMAL == "minimal"
