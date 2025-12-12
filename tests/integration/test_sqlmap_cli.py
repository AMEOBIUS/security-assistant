"""
Integration tests for SQLMap CLI commands.
"""

import os
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from security_assistant.cli_sqlmap import (
    handle_sqlmap_custom,
    handle_sqlmap_full,
    handle_sqlmap_quick,
    register_sqlmap_commands,
)


class TestSQLMapCLI:
    """Test SQLMap CLI commands."""
    
    def test_register_sqlmap_commands(self):
        """Test that CLI commands are registered correctly."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Test")
        subparsers = parser.add_subparsers(title="SQLMap commands", dest="command")
        
        # This should not raise an exception
        register_sqlmap_commands(subparsers)
        
        # Verify commands are registered by checking if we can parse them
        # Test quick command
        args1 = parser.parse_args(["sqlmap-quick", "--url", "http://test.com", "--params", "id"])
        assert hasattr(args1, 'func')
        
        # Test full command
        args2 = parser.parse_args(["sqlmap-full", "--url", "http://test.com", "--params", "id"])
        assert hasattr(args2, 'func')
        
        # Test custom command
        args3 = parser.parse_args(["sqlmap-custom", "--url", "http://test.com", "--params", "id", "--level", "2"])
        assert hasattr(args3, 'func')
    
    def test_sqlmap_quick_command(self):
        """Test sqlmap-quick command."""
        args = Mock()
        args.url = "http://example.com/test.php"
        args.params = "id"
        args.data = None
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.quick_scan.return_value = {
                "target": "http://example.com/test.php",
                "status": "completed",
                "vulnerabilities": [],
                "timestamp": "2025-12-11T12:00:00"
            }
            mock_scanner_class.return_value = mock_scanner
            
            # Capture output
            from unittest.mock import patch as mock_patch
            with mock_patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                handle_sqlmap_quick(args)
                
                output = mock_stdout.getvalue()
                assert "QUICK SCAN" in output
                assert "http://example.com/test.php" in output
                assert "No vulnerabilities found" in output
    
    def test_sqlmap_full_command(self):
        """Test sqlmap-full command."""
        args = Mock()
        args.url = "http://example.com/login.php"
        args.params = "username,password"
        args.data = None
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.full_scan.return_value = {
                "target": "http://example.com/login.php",
                "status": "completed",
                "vulnerabilities": [],
                "timestamp": "2025-12-11T12:00:00"
            }
            mock_scanner_class.return_value = mock_scanner
            
            # Capture output
            from unittest.mock import patch as mock_patch
            with mock_patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                handle_sqlmap_full(args)
                
                output = mock_stdout.getvalue()
                assert "FULL SCAN" in output
                assert "http://example.com/login.php" in output
    
    def test_sqlmap_custom_command(self):
        """Test sqlmap-custom command."""
        args = Mock()
        args.url = "http://example.com/api"
        args.params = "id"
        args.data = "username=admin&password=test"
        args.level = 3
        args.risk = 2
        args.batch = True
        args.output = "json"
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.scan.return_value = {
                "target": "http://example.com/api",
                "status": "completed",
                "vulnerabilities": [
                    {
                        "type": "sql_injection",
                        "parameter": "id",
                        "severity": "HIGH",
                        "description": "GET parameter 'id' is vulnerable",
                        "payload": "id=1' OR 1=1 -- -"
                    }
                ],
                "timestamp": "2025-12-11T12:00:00"
            }
            mock_scanner_class.return_value = mock_scanner
            
            # Capture output
            from unittest.mock import patch as mock_patch
            with mock_patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                handle_sqlmap_custom(args)
                
                output = mock_stdout.getvalue()
                assert "CUSTOM SCAN" in output
                assert "http://example.com/api" in output
                assert "Vulnerability #1" in output
                assert "sql_injection" in output
                assert "HIGH" in output
    
    def test_sqlmap_error_handling(self):
        """Test error handling in CLI commands."""
        args = Mock()
        args.url = "http://example.com/test.php"
        args.params = "id"
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.quick_scan.side_effect = Exception("Scan failed")
            mock_scanner_class.return_value = mock_scanner
            
            with pytest.raises(SystemExit) as exc_info:
                handle_sqlmap_quick(args)
            
            assert exc_info.value.code == 1


class TestSQLMapCLIIntegration:
    """Test SQLMap CLI integration with scanner."""
    
    def test_quick_scan_integration(self):
        """Test integration between CLI and scanner for quick scan."""
        args = Mock()
        args.url = "http://test.com/vuln.php"
        args.params = "id"
        args.data = None
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.quick_scan.return_value = {
                "target": "http://test.com/vuln.php",
                "status": "completed",
                "vulnerabilities": [
                    {
                        "type": "sql_injection",
                        "parameter": "id",
                        "severity": "CRITICAL",
                        "description": "Blind SQL injection vulnerability",
                        "payload": "id=1 AND SLEEP(5)"
                    }
                ],
                "timestamp": "2025-12-11T12:00:00"
            }
            mock_scanner_class.return_value = mock_scanner
            
            # Capture output
            from unittest.mock import patch as mock_patch
            with mock_patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                handle_sqlmap_quick(args)
                
                output = mock_stdout.getvalue()
                assert "Found 1 vulnerabilities" in output
                assert "CRITICAL" in output
                assert "Blind SQL injection" in output
                assert "RECOMMENDATION" in output
    
    def test_parameter_parsing(self):
        """Test parameter parsing in CLI commands."""
        # Test single parameter
        args1 = Mock()
        args1.params = "id"
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.quick_scan.return_value = {"vulnerabilities": []}
            mock_scanner_class.return_value = mock_scanner
            
            handle_sqlmap_quick(args1)
            
            # Verify params were passed as list
            call_args = mock_scanner.quick_scan.call_args
            assert call_args[1]['params'] == ["id"]
        
        # Test multiple parameters
        args2 = Mock()
        args2.params = "id,page,user"
        
        with patch('security_assistant.cli_sqlmap.SQLMapScanner') as mock_scanner_class:
            mock_scanner = Mock()
            mock_scanner.quick_scan.return_value = {"vulnerabilities": []}
            mock_scanner_class.return_value = mock_scanner
            
            handle_sqlmap_quick(args2)
            
            # Verify params were split correctly
            call_args = mock_scanner.quick_scan.call_args
            assert call_args[1]['params'] == ["id", "page", "user"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
