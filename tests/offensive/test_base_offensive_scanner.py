"""
Unit tests for base offensive scanner.
"""

from unittest.mock import Mock, patch

import pytest

from security_assistant.offensive.base_offensive_scanner import (
    AuthorizationRequiredError,
    OffensiveScanner,
    TargetNotAuthorizedError,
)


class TestOffensiveScanner:
    """Test OffensiveScanner base class."""
    
    def test_abstract_methods(self):
        """Test that abstract methods are properly defined."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            OffensiveScanner()
    
    def test_tos_required(self):
        """Test ToS requirement."""
        # Mock scanner that doesn't accept ToS
        with patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_service = Mock()
            mock_service.check_tos_accepted.return_value = False
            mock_auth.return_value = mock_service
            
            # Create concrete scanner for testing
            class TestScanner(OffensiveScanner):
                @property
                def scanner_type(self):
                    return "test"
                
                @property
                def risk_level(self):
                    return "LOW"
                
                def scan(self, target, **kwargs):
                    return {}
            
            with pytest.raises(AuthorizationRequiredError):
                TestScanner()
    
    def test_authorization_check(self):
        """Test target authorization check."""
        with patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_service = Mock()
            mock_service.check_tos_accepted.return_value = True
            mock_service.is_authorized.return_value = False
            mock_auth.return_value = mock_service
            
            class TestScanner(OffensiveScanner):
                @property
                def scanner_type(self):
                    return "test"
                
                @property
                def risk_level(self):
                    return "LOW"
                
                def scan(self, target, **kwargs):
                    self._check_authorization(target)
                    return {}
            
            scanner = TestScanner()
            
            with pytest.raises(TargetNotAuthorizedError):
                scanner.scan("unauthorized.com")
    
    def test_safety_recommendations(self):
        """Test safety recommendations."""
        with patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_service = Mock()
            mock_service.check_tos_accepted.return_value = True
            mock_auth.return_value = mock_service
            
            class TestScanner(OffensiveScanner):
                @property
                def scanner_type(self):
                    return "network"
                
                @property
                def risk_level(self):
                    return "HIGH"
                
                def scan(self, target, **kwargs):
                    return {}
            
            scanner = TestScanner()
            recommendations = scanner.get_safety_recommendations()
            
            assert len(recommendations) == 5
            assert "HIGH" in recommendations[2]
            assert "network" in recommendations[1]


class TestOffensiveScannerAbstractMethods:
    """Test abstract method enforcement."""
    
    def test_missing_scan_method(self):
        """Test missing scan method."""
        with patch('security_assistant.offensive.authorization.AuthorizationService') as mock_auth:
            mock_service = Mock()
            mock_service.check_tos_accepted.return_value = True
            mock_auth.return_value = mock_service
            
            class IncompleteScanner(OffensiveScanner):
                @property
                def scanner_type(self):
                    return "test"
                
                # Missing scan method and risk_level
            
            with pytest.raises(TypeError):
                IncompleteScanner()
    
    def test_missing_properties(self):
        """Test missing required properties."""
        with patch('security_assistant.offensive.authorization.AuthorizationService') as mock_auth:
            mock_service = Mock()
            mock_service.check_tos_accepted.return_value = True
            mock_auth.return_value = mock_service
            
            class IncompleteScanner(OffensiveScanner):
                def scan(self, target, **kwargs):
                    return {}
                
                # Missing scanner_type and risk_level properties
            
            with pytest.raises(TypeError):
                IncompleteScanner()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
