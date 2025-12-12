"""Tests for Safety Checker."""

import pytest

from security_assistant.poc.safety_checker import PoCSafetyError, SafetyChecker


@pytest.fixture
def checker():
    return SafetyChecker()

def test_safe_code(checker):
    """Test validation of safe code."""
    code = """
    import requests
    print("Hello World")
    """
    warnings = checker.validate(code)
    assert len(warnings) == 0

def test_dangerous_rm(checker):
    """Test detection of rm -rf."""
    code = "os.system('rm -rf /')"
    with pytest.raises(PoCSafetyError, match="File deletion"):
        checker.validate(code)

def test_dangerous_drop_table(checker):
    """Test detection of DROP TABLE."""
    code = "cursor.execute('DROP TABLE users')"
    with pytest.raises(PoCSafetyError, match="Database drop"):
        checker.validate(code)

def test_warning_patterns(checker):
    """Test detection of patterns that generate warnings."""
    code = "os.system('ls -la')"
    warnings = checker.validate(code)
    assert len(warnings) == 1
    assert "os.system" in warnings[0]

def test_sanitize_payload(checker):
    """Test payload sanitization."""
    payload = "admin'; DROP TABLE users; --"
    sanitized = checker.sanitize_payload(payload)
    assert "DROP TABLE" not in sanitized
    assert "SELECT 1" in sanitized
