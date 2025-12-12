"""
Test WAF detection functionality.
"""

from unittest.mock import MagicMock, patch

from security_assistant.offensive.authorization import AuthorizationService
from security_assistant.offensive.waf.detector import WAFDetector


def test_waf_detector_initialization():
    """Test WAF detector initialization."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    detector = WAFDetector(auth_service=auth_service)
    
    assert detector.timeout == 30
    assert "Mozilla" in detector.user_agent
    assert len(detector.WAF_SIGNATURES) == 10
    assert "Cloudflare" in detector.WAF_SIGNATURES


def test_waf_detector_validation():
    """Test WAF detector validation."""
    auth_service = AuthorizationService()
    # Don't accept ToS to test validation
    
    # Should still initialize but log warning
    detector = WAFDetector(auth_service=auth_service)
    assert detector is not None


def test_waf_detector_signatures():
    """Test WAF signatures database."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    detector = WAFDetector(auth_service=auth_service)
    signatures = detector.get_waf_signatures()
    
    assert "Cloudflare" in signatures
    assert "AWS WAF" in signatures
    assert "ModSecurity" in signatures
    assert "Imperva" in signatures
    assert "Akamai" in signatures
    
    # Check Cloudflare signatures
    cloudflare = signatures["Cloudflare"]
    assert "cf-ray" in str(cloudflare["headers"])
    assert "__cfduid" in str(cloudflare["cookies"])


@patch('requests.Session.get')
def test_passive_detection(mock_get):
    """Test passive WAF detection."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock response with Cloudflare headers
    mock_response = MagicMock()
    mock_response.headers = {
        "cf-ray": "123456",
        "server": "cloudflare"
    }
    mock_response.cookies = []
    mock_get.return_value = mock_response
    
    detector = WAFDetector(auth_service=auth_service)
    result = detector._passive_detection("https://example.com")
    
    assert result["detected"]
    assert result["waf_type"] == "Cloudflare"
    assert result["confidence"] in ["high", "medium"]
    assert len(result["evidence"]) >= 1


@patch('requests.Session.get')
def test_active_detection(mock_get):
    """Test active WAF detection."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock response that blocks SQLi payload
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Access Denied - Request blocked by security rules"
    mock_get.return_value = mock_response
    
    detector = WAFDetector(auth_service=auth_service)
    result = detector._active_detection("https://example.com", max_tests=1)
    
    assert result["detected"]
    assert result["method"] == "active"
    assert len(result["evidence"]) >= 1


@patch('requests.Session.get')
def test_error_page_analysis(mock_get):
    """Test error page analysis."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock 404 response with Cloudflare error page
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "404 Not Found - Cloudflare"
    mock_get.return_value = mock_response
    
    detector = WAFDetector(auth_service=auth_service)
    result = detector._error_page_analysis("https://example.com")
    
    assert result["detected"]
    assert result["waf_type"] == "Cloudflare"
    assert result["method"] == "error_analysis"


@patch('requests.Session.get')
def test_comprehensive_detection(mock_get):
    """Test comprehensive WAF detection."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock response with Cloudflare headers
    mock_response = MagicMock()
    mock_response.headers = {"cf-ray": "123456"}
    mock_response.cookies = []
    mock_get.return_value = mock_response
    
    detector = WAFDetector(auth_service=auth_service)
    result = detector.detect_waf("https://example.com")
    
    assert result["detected"]
    assert result["waf_type"] == "Cloudflare"
    assert result["method"] in ["passive", "active", "error_analysis", "comprehensive"]


@patch('requests.Session.get')
def test_no_waf_detected(mock_get):
    """Test when no WAF is detected."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock normal response without WAF headers
    mock_response = MagicMock()
    mock_response.headers = {"server": "nginx"}
    mock_response.cookies = []
    mock_get.return_value = mock_response
    
    detector = WAFDetector(auth_service=auth_service)
    result = detector.detect_waf("https://example.com", test_payloads=False)
    
    assert not result["detected"]
    assert result["waf_type"] == "None"
    assert result["confidence"] == "low"


def test_url_validation():
    """Test URL validation."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    detector = WAFDetector(auth_service=auth_service)
    
    assert detector.validate_target("https://example.com")
    assert detector.validate_target("http://example.com/path")
    assert not detector.validate_target("example.com")
    assert not detector.validate_target("")


def test_batch_detection():
    """Test batch WAF detection."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    detector = WAFDetector(auth_service=auth_service)
    
    # Test with mock URLs (will fail but test the batch functionality)
    urls = ["https://example.com", "https://test.com"]
    results = detector.detect_waf_batch(urls)
    
    assert len(results) == 2
    assert all("url" in result for result in results)


if __name__ == "__main__":
    test_waf_detector_initialization()
    test_waf_detector_validation()
    test_waf_detector_signatures()
    test_passive_detection()
    test_active_detection()
    test_error_page_analysis()
    test_comprehensive_detection()
    test_no_waf_detected()
    test_url_validation()
    test_batch_detection()
    print("✅ All WAF detector tests passed!")
