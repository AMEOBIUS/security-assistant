"""
Unit tests for Nmap scanner.
"""

import os
import subprocess
import sys
from unittest.mock import Mock, patch

import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from security_assistant.offensive.scanners.nmap_scanner import (
    NmapNotInstalledError,
    NmapScanner,
    NmapScannerError,
)


class TestNmapScanner:
    """Test NmapScanner class."""
    
    def test_initialization_without_nmap(self):
        """Test initialization when Nmap not installed."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.side_effect = FileNotFoundError("nmap not found")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            with pytest.raises(NmapNotInstalledError):
                NmapScanner()
    
    def test_initialization_with_nmap(self):
        """Test successful initialization."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Nmap version 7.94",
                stderr=""
            )
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            assert scanner is not None
    
    def test_scan_without_authorization(self):
        """Test scan without authorization."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.side_effect = Exception("Not authorized")
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            with pytest.raises(Exception, match="Not authorized"):
                scanner.scan("192.168.1.1")
    
    def test_build_nmap_command(self):
        """Test Nmap command building."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            cmd = scanner._build_nmap_command(
                "192.168.1.1",
                ports=[22, 80, 443],
                service_detection=True,
                os_detection=False,
                timing=3
            )
            
            assert "nmap" in cmd
            assert "--xml" in cmd
            assert "-T" in cmd
            assert "3" in cmd
            assert "-p" in cmd
            assert "22,80,443" in cmd
            assert "-sV" in cmd
            assert "192.168.1.1" in cmd
    
    def test_parse_nmap_xml(self):
        """Test Nmap XML parsing."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Sample Nmap XML output
            xml_output = """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -oX - scanme.nmap.org" start="1765410482" version="7.94" xmloutputversion="1.04">
  <host starttime="1765410482" endtime="1765410483">
    <status state="up" reason="syn-ack"/>
    <address addr="45.33.32.156" addrtype="ipv4"/>
    <hostnames>
      <hostname name="scanme.nmap.org" type="user"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open" reason="syn-ack" reason_ttl="55"/>
        <service name="ssh" product="OpenSSH" version="8.2p1 Ubuntu 4ubuntu0.1" extrainfo="Ubuntu Linux; protocol 2.0" method="probed" conf="10"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open" reason="syn-ack" reason_ttl="55"/>
        <service name="http" product="Apache httpd" version="2.4.41" extrainfo="(Ubuntu)" method="probed" conf="10"/>
      </port>
    </ports>
    <os>
      <osmatch name="Linux 3.13 - 4.8" accuracy="100" line="100%" />
    </os>
  </host>
</nmaprun>"""
            
            result = scanner._parse_nmap_xml(xml_output)
            
            assert "targets" in result
            assert len(result["targets"]) == 1
            assert result["targets"][0]["addresses"][0]["addr"] == "45.33.32.156"
            assert len(result["targets"][0]["ports"]) == 2
            assert result["targets"][0]["ports"][0]["portid"] == "22"
            assert result["targets"][0]["ports"][0]["service"]["name"] == "ssh"
    
    def test_quick_scan(self):
        """Test quick scan method."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Mock scan method
            with patch.object(scanner, 'scan') as mock_scan:
                mock_scan.return_value = {"targets": []}
                
                result = scanner.quick_scan("192.168.1.1")
                
                # Verify scan was called with correct parameters
                mock_scan.assert_called_once()
                call_args = mock_scan.call_args
                assert call_args[1]['ports'] == "1-100"
                assert call_args[1]['service_detection'] is False
                assert call_args[1]['timing'] == 2
    
    def test_full_scan(self):
        """Test full scan method."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Mock scan method
            with patch.object(scanner, 'scan') as mock_scan:
                mock_scan.return_value = {"targets": []}
                
                result = scanner.full_scan("192.168.1.1")
                
                # Verify scan was called with correct parameters
                call_args = mock_scan.call_args
                assert call_args[1]['ports'] == "1-65535"
                assert call_args[1]['service_detection'] is True
                assert call_args[1]['os_detection'] is True
                assert call_args[1]['timing'] == 4
    
    def test_vulnerability_scan(self):
        """Test vulnerability scan method."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Mock scan method
            with patch.object(scanner, 'scan') as mock_scan:
                mock_scan.return_value = {"targets": []}
                
                result = scanner.vulnerability_scan("192.168.1.1")
                
                # Verify scan was called with correct parameters
                call_args = mock_scan.call_args
                assert call_args[1]['ports'] == "1-1000"
                assert call_args[1]['service_detection'] is True
                assert call_args[1]['nse_scripts'] == ["vuln", "exploit", "malware"]


class TestNmapErrorHandling:
    """Test Nmap error handling."""
    
    def test_scan_failed(self):
        """Test scan failure handling."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Mock subprocess to fail
            with patch('subprocess.run') as mock_scan_run:
                mock_scan_run.return_value = Mock(
                    returncode=1,
                    stdout="",
                    stderr="Host seems down"
                )
                
                with pytest.raises(Exception, match="Nmap scan failed"):
                    scanner.scan("192.168.1.1")
    
    def test_scan_timeout(self):
        """Test scan timeout handling."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Mock subprocess to timeout
            with patch('subprocess.run') as mock_scan_run:
                mock_scan_run.side_effect = subprocess.TimeoutExpired("nmap", 300)
                
                with pytest.raises(Exception, match="timed out"):
                    scanner.scan("192.168.1.1")
    
    def test_xml_parse_error(self):
        """Test XML parse error handling."""
        with patch('subprocess.run') as mock_run, \
             patch('security_assistant.offensive.base_offensive_scanner.AuthorizationService') as mock_auth:
            mock_run.return_value = Mock(returncode=0, stdout="Nmap version 7.94")
            
            # Mock authorization service
            mock_auth_service = Mock()
            mock_auth_service.check_tos_accepted.return_value = True
            mock_auth_service.is_authorized.return_value = True
            mock_auth.return_value = mock_auth_service
            
            scanner = NmapScanner()
            
            # Mock subprocess to return invalid XML
            with patch('subprocess.run') as mock_scan_run:
                mock_scan_run.return_value = Mock(
                    returncode=0,
                    stdout="Invalid XML",
                    stderr=""
                )
                
                with pytest.raises(NmapScannerError, match="Failed to parse"):
                    scanner.scan("192.168.1.1")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
