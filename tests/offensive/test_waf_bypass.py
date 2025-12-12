
import pytest
from unittest.mock import Mock
from security_assistant.offensive.waf.bypass import WAFBypassEngine
from security_assistant.offensive.authorization import AuthorizationService

@pytest.fixture
def auth_service():
    service = Mock(spec=AuthorizationService)
    service.check_tos_accepted.return_value = True
    return service

def test_bypass_engine_initialization(auth_service):
    """Test engine initialization."""
    engine = WAFBypassEngine(auth_service=auth_service)
    assert engine.auth_service == auth_service
    assert "url" in engine.encoding_techniques

def test_url_encoding(auth_service):
    """Test URL encoding technique."""
    engine = WAFBypassEngine(auth_service=auth_service)
    payload = "SELECT * FROM users"
    encoded = engine._apply_technique(payload, "url")
    assert encoded == "SELECT%20%2A%20FROM%20users"

def test_base64_encoding(auth_service):
    """Test Base64 encoding technique."""
    engine = WAFBypassEngine(auth_service=auth_service)
    payload = "admin"
    encoded = engine._apply_technique(payload, "base64")
    assert encoded == "YWRtaW4="

def test_hex_encoding(auth_service):
    """Test Hex encoding technique."""
    engine = WAFBypassEngine(auth_service=auth_service)
    payload = "AB"
    encoded = engine._apply_technique(payload, "hex")
    assert encoded == "4142"

def test_dispatch_mechanism(auth_service):
    """Test that the dictionary dispatch works for all keys."""
    engine = WAFBypassEngine(auth_service=auth_service)
    payload = "test"
    
    # Test all registered techniques
    for technique in engine._technique_map.keys():
        result = engine._apply_technique(payload, technique)
        assert result is not None
        assert isinstance(result, str)

def test_unknown_technique(auth_service):
    """Test graceful handling of unknown techniques."""
    engine = WAFBypassEngine(auth_service=auth_service)
    payload = "test"
    result = engine._apply_technique(payload, "nonexistent_tech")
    assert result == payload

def test_obfuscate_payload_random(auth_service):
    """Test random obfuscation."""
    engine = WAFBypassEngine(auth_service=auth_service)
    payload = "UNION SELECT"
    results = engine.obfuscate_payload(payload, max_techniques=2)
    assert len(results) > 0
    assert isinstance(results[0], str)
