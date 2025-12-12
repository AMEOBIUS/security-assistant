"""
Unit tests for SQLMap scanner.
"""

import os
import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from security_assistant.offensive.scanners.sqlmap_scanner import (
    SQLMapNotInstalledError,
    SQLMapScanner,
    SQLMapScannerError,
)


class TestSQLMapScanner:
    """Test SQLMapScanner class."""
    
    def test_initialization_without_sqlmap(self):
        """Test initialization when SQLMap not installed."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.side_effect = FileNotFoundError("sqlmap not found")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            with pytest.raises(SQLMapNotInstalledError):
                SQLMapScanner()
    
    def test_initialization_with_sqlmap(self):
        """Test successful initialization."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="SQLMap version 1.7.8",
                stderr=""
            )
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            assert scanner is not None
            assert scanner.scanner_type == "web"
            assert scanner.risk_level == "HIGH"
    
    def test_scan_without_authorization(self):
        """Test scan without authorization."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.side_effect = Exception("Not authorized")
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            with pytest.raises(Exception, match="Not authorized"):
                scanner.scan("http://example.com/test.php?id=1")
    
    def test_build_sqlmap_command(self):
        """Test SQLMap command building."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            cmd = scanner._build_sqlmap_command(
                "http://example.com/test.php",
                params=["id", "page"],
                data="username=admin&password=test",
                level=2,
                risk=1,
                batch=True,
                output_format="json"
            )
            
            assert "sqlmap" in cmd
            assert "-u" in cmd
            assert "http://example.com/test.php" in cmd
            assert "-p" in cmd
            assert "id" in cmd
            assert "page" in cmd
            assert "--data" in cmd
            # Check that data is present (may be split into multiple elements)
            data_str = ' '.join(cmd)
            assert "username=admin" in data_str
            assert "--level" in cmd
            assert "2" in cmd
            assert "--risk" in cmd
            assert "1" in cmd
            assert "--batch" in cmd
            assert "--json" in cmd
    
    def test_parse_json_output(self):
        """Test SQLMap JSON parsing."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            # Sample SQLMap JSON output
            json_output = """{
                "target": "http://example.com/test.php",
                "vulnerabilities": [
                    {
                        "type": "sql_injection",
                        "parameter": "id",
                        "severity": "HIGH",
                        "description": "GET parameter 'id' is vulnerable to SQL injection",
                        "payload": "id=1' OR 1=1 ---"
                    }
                ]
            }"""
            
            result = scanner._parse_json_output(json_output)
            
            assert "target" in result
            assert result["target"] == "http://example.com/test.php"
            assert "vulnerabilities" in result
            assert len(result["vulnerabilities"]) == 1
            assert result["vulnerabilities"][0]["parameter"] == "id"
    
    def test_quick_scan(self):
        """Test quick scan method."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            # Mock scan method
            with patch.object(scanner, 'scan') as mock_scan:
                mock_scan.return_value = {"vulnerabilities": []}
                
                result = scanner.quick_scan("http://example.com/test.php", params="id")
                
                # Verify scan was called with correct parameters
                mock_scan.assert_called_once()
                call_args = mock_scan.call_args
                assert call_args[1]['params'] == "id"
                assert call_args[1]['level'] == 1
                assert call_args[1]['risk'] == 1
                assert call_args[1]['batch'] is True
    
    def test_full_scan(self):
        """Test full scan method."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            # Mock scan method
            with patch.object(scanner, 'scan') as mock_scan:
                mock_scan.return_value = {"vulnerabilities": []}
                
                result = scanner.full_scan("http://example.com/test.php", params="id")
                
                # Verify scan was called with correct parameters
                call_args = mock_scan.call_args
                assert call_args[1]['params'] == "id"
                assert call_args[1]['level'] == 5
                assert call_args[1]['risk'] == 3
                assert call_args[1]['batch'] is True


class TestSQLMapErrorHandling:
    """Test SQLMap error handling."""
    
    def test_scan_failed(self):
        """Test scan failure handling."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            # Mock subprocess to fail
            with patch('subprocess.run') as mock_scan_run:
                mock_scan_run.return_value = Mock(
                    returncode=1,
                    stdout="",
                    stderr="Target URL not responding"
                )
                
                with pytest.raises(Exception, match="SQLMap scan failed"):
                    scanner.scan("http://example.com/test.php", params="id")
    
    def test_scan_timeout(self):
        """Test scan timeout handling."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            # Mock subprocess to timeout
            with patch('subprocess.run') as mock_scan_run:
                mock_scan_run.side_effect = subprocess.TimeoutExpired("sqlmap", 600)
                
                with pytest.raises(Exception, match="timed out"):
                    scanner.scan("http://example.com/test.php", params="id")
    
    def test_json_parse_error(self):
        """Test JSON parse error handling."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="SQLMap version 1.7.8")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = SQLMapScanner()
            
            # Mock subprocess to return invalid JSON
            with patch('subprocess.run') as mock_scan_run:
                mock_scan_run.return_value = Mock(
                    returncode=0,
                    stdout="Invalid JSON",
                    stderr=""
                )
                
                with pytest.raises(SQLMapScannerError, match="Failed to parse"):
                    scanner.scan("http://example.com/test.php", params="id", output_format="json")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
