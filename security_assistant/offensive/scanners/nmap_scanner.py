"""
Nmap Scanner Integration

Offensive security scanner for network discovery and port scanning using Nmap.

Features:
- Network discovery (ping scan)
- Port scanning (TCP/UDP)
- Service detection
- OS fingerprinting
- NSE vulnerability scripts
- XML output parsing
- Integration with authorization system

Requirements:
- Nmap must be installed on the system
- Python 3.11+

Example usage:
    scanner = NmapScanner()
    result = scanner.scan("192.168.1.1", ports="22,80,443", service_detection=True)
"""

import logging
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union

from security_assistant.offensive.base_offensive_scanner import OffensiveScanner

logger = logging.getLogger(__name__)


class NmapScannerError(Exception):
    """Base exception for Nmap scanner errors."""
    pass


class NmapNotInstalledError(NmapScannerError):
    """Nmap is not installed on the system."""
    pass


class NmapScanFailedError(NmapScannerError):
    """Nmap scan failed to execute."""
    pass


class NmapScanner(OffensiveScanner):
    """
    Nmap security scanner for network discovery and port scanning.
    
    Inherits from OffensiveScanner for authorization and ToS enforcement.
    """
    
    def __init__(self):
        """Initialize Nmap scanner."""
        super().__init__()
        self._check_nmap_installation()
        
    @property
    def scanner_type(self) -> str:
        """Type of offensive scanner."""
        return "network"
    
    @property
    def risk_level(self) -> str:
        """Risk level of scanner."""
        return "MEDIUM"
    
    def _check_nmap_installation(self):
        """Check if Nmap is installed on the system."""
        try:
            result = subprocess.run(
                ["nmap", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise NmapNotInstalledError(
                    "Nmap is not installed. Please install Nmap from https://nmap.org/ "
                    "and ensure it's in your PATH."
                )
            
            logger.info(f"Nmap installed: {result.stdout.strip()}")
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise NmapNotInstalledError(  # noqa: B904
                "Nmap is not installed or not in PATH. "
                "Install from https://nmap.org/"
            )
    
    def scan(
        self,
        target: str,
        ports: Optional[Union[str, List[str]]] = None,
        service_detection: bool = False,
        os_detection: bool = False,
        timing: int = 3,
        nse_scripts: Optional[List[str]] = None,
        **kwargs
    ) -> Dict:
        """
        Perform Nmap scan on target.
        
        Args:
            target: Target IP, hostname, or CIDR range
            ports: Ports to scan (e.g., "22,80,443" or [22, 80, 443])
            service_detection: Enable service detection (-sV)
            os_detection: Enable OS detection (-O)
            timing: Timing template (0-5, where 3 is normal)
            nse_scripts: NSE scripts to run
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with scan results
            
        Raises:
            TargetNotAuthorizedError: If target not authorized
            NmapScannerError: If scan fails
        """
        # Check authorization
        self._check_authorization(target)
        
        # Build Nmap command
        cmd = self._build_nmap_command(
            target,
            ports=ports,
            service_detection=service_detection,
            os_detection=os_detection,
            timing=timing,
            nse_scripts=nse_scripts
        )
        
        # Log offensive action
        self._log_offensive_action("nmap_scan", target, f"Command: {' '.join(cmd)}")
        
        try:
            # Execute Nmap
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise NmapScanFailedError(
                    f"Nmap scan failed with return code {result.returncode}: {error_msg}"
                )
            
            # Parse XML output
            scan_result = self._parse_nmap_xml(result.stdout)
            
            # Standardize result
            return self._standardize_result(scan_result)
            
        except subprocess.TimeoutExpired:
            raise NmapScanFailedError("Nmap scan timed out after 5 minutes")  # noqa: B904
        except Exception as e:
            raise NmapScanFailedError(f"Nmap scan failed: {str(e)}")  # noqa: B904
    
    def _build_nmap_command(
        self,
        target: str,
        ports: Optional[Union[str, List[str]]] = None,
        service_detection: bool = False,
        os_detection: bool = False,
        timing: int = 3,
        nse_scripts: Optional[List[str]] = None
    ) -> List[str]:
        """
        Build Nmap command line.
        
        Args:
            target: Target to scan
            ports: Ports to scan
            service_detection: Enable service detection
            os_detection: Enable OS detection
            timing: Timing template
            nse_scripts: NSE scripts to run
            
        Returns:
            List of command arguments
        """
        cmd = ["nmap", "--xml"]
        
        # Add timing template
        cmd.extend(["-T", str(timing)])
        
        # Add ports if specified
        if ports:
            if isinstance(ports, list):
                ports_str = ",".join(str(p) for p in ports)
            else:
                ports_str = str(ports)
            cmd.extend(["-p", ports_str])
        
        # Add service detection
        if service_detection:
            cmd.append("-sV")
        
        # Add OS detection
        if os_detection:
            cmd.append("-O")
        
        # Add NSE scripts
        if nse_scripts:
            for script in nse_scripts:
                cmd.extend(["--script", script])
        
        # Add target
        cmd.append(target)
        
        return cmd
    
    def _parse_nmap_xml(self, xml_output: str) -> Dict:
        """
        Parse Nmap XML output.
        
        Args:
            xml_output: XML output from Nmap
            
        Returns:
            Dictionary with parsed results
            
        Raises:
            NmapScannerError: If XML parsing fails
        """
        try:
            root = ET.fromstring(xml_output)
            
            result = {
                "targets": [],
                "summary": {
                    "start_time": root.attrib.get("start"),
                    "version": root.attrib.get("version"),
                    "xml_output_version": root.attrib.get("xmloutputversion")
                }
            }
            
            # Parse each host
            for host_elem in root.findall("host"):
                target = self._parse_host_element(host_elem)
                result["targets"].append(target)
            
            return result
            
        except ET.ParseError as e:
            raise NmapScannerError(f"Failed to parse Nmap XML output: {str(e)}")  # noqa: B904
    
    def _parse_host_element(self, host_elem) -> Dict:
        """Parse individual host element from Nmap XML."""
        host = {
            "addresses": [],
            "ports": [],
            "os": None,
            "hostnames": [],
            "status": {
                "state": host_elem.find("status").attrib.get("state"),
                "reason": host_elem.find("status").attrib.get("reason")
            }
        }
        
        # Parse addresses
        for addr_elem in host_elem.findall("address"):
            host["addresses"].append({
                "addr": addr_elem.attrib.get("addr"),
                "addrtype": addr_elem.attrib.get("addrtype")
            })
        
        # Parse hostnames
        for hostname_elem in host_elem.findall("hostnames/hostname"):
            host["hostnames"].append({
                "name": hostname_elem.attrib.get("name"),
                "type": hostname_elem.attrib.get("type")
            })
        
        # Parse ports
        for port_elem in host_elem.findall("ports/port"):
            port = self._parse_port_element(port_elem)
            host["ports"].append(port)
        
        # Parse OS
        os_elem = host_elem.find("os")
        if os_elem is not None:
            host["os"] = self._parse_os_element(os_elem)
        
        return host
    
    def _parse_port_element(self, port_elem) -> Dict:
        """Parse individual port element from Nmap XML."""
        port = {
            "protocol": port_elem.attrib.get("protocol"),
            "portid": port_elem.attrib.get("portid"),
            "state": port_elem.find("state").attrib.get("state"),
            "service": None,
            "scripts": []
        }
        
        # Parse service
        service_elem = port_elem.find("service")
        if service_elem is not None:
            port["service"] = {
                "name": service_elem.attrib.get("name"),
                "product": service_elem.attrib.get("product"),
                "version": service_elem.attrib.get("version"),
                "extrainfo": service_elem.attrib.get("extrainfo"),
                "ostype": service_elem.attrib.get("ostype"),
                "method": service_elem.attrib.get("method"),
                "conf": service_elem.attrib.get("conf")
            }
        
        # Parse scripts
        for script_elem in port_elem.findall("script"):
            script = {
                "id": script_elem.attrib.get("id"),
                "output": script_elem.attrib.get("output")
            }
            port["scripts"].append(script)
        
        return port
    
    def _parse_os_element(self, os_elem) -> Dict:
        """Parse OS element from Nmap XML."""
        os_info = {
            "osmatches": [],
            "ports_used": [],
            "os_fingerprint": None
        }
        
        # Parse OS matches
        for osmatch_elem in os_elem.findall("osmatch"):
            osmatch = {
                "name": osmatch_elem.attrib.get("name"),
                "accuracy": osmatch_elem.attrib.get("accuracy"),
                "line": osmatch_elem.attrib.get("line")
            }
            os_info["osmatches"].append(osmatch)
        
        # Parse ports used
        for portused_elem in os_elem.findall("portused"):
            os_info["ports_used"].append({
                "proto": portused_elem.attrib.get("proto"),
                "portid": portused_elem.attrib.get("portid"),
                "state": portused_elem.attrib.get("state")
            })
        
        # Parse OS fingerprint
        osfingerprint_elem = os_elem.find("osfingerprint")
        if osfingerprint_elem is not None:
            os_info["os_fingerprint"] = osfingerprint_elem.attrib.get("fingerprint")
        
        return os_info
    
    def _standardize_result(self, raw_result: Dict) -> Dict:
        """
        Convert Nmap results to standardized format.
        
        Args:
            raw_result: Raw Nmap scan results
            
        Returns:
            Standardized result dictionary
        """
        standardized = super()._standardize_result(raw_result)
        
        # Add Nmap-specific information
        standardized.update({
            "scanner_specific": {
                "nmap_version": raw_result["summary"].get("version"),
                "targets_scanned": len(raw_result["targets"]),
                "scan_type": "nmap"
            }
        })
        
        return standardized
    
    def quick_scan(self, target: str) -> Dict:
        """
        Perform quick Nmap scan (top 100 ports, no service detection).
        
        Args:
            target: Target to scan
            
        Returns:
            Scan results
        """
        return self.scan(
            target=target,
            ports="1-100",
            service_detection=False,
            os_detection=False,
            timing=2  # Faster timing
        )
    
    def full_scan(self, target: str) -> Dict:
        """
        Perform comprehensive Nmap scan.
        
        Args:
            target: Target to scan
            
        Returns:
            Scan results
        """
        return self.scan(
            target=target,
            ports="1-65535",
            service_detection=True,
            os_detection=True,
            timing=4  # Slower, more thorough
        )
    
    def vulnerability_scan(self, target: str) -> Dict:
        """
        Perform vulnerability scan using NSE scripts.
        
        Args:
            target: Target to scan
            
        Returns:
            Scan results with vulnerabilities
        """
        return self.scan(
            target=target,
            ports="1-1000",
            service_detection=True,
            nse_scripts=["vuln", "exploit", "malware"]
        )


# Example usage
if __name__ == "__main__":
    try:
        scanner = NmapScanner()
        
        # Quick scan
        result = scanner.quick_scan("scanme.nmap.org")
        print(f"Scanned {len(result['targets'])} targets")
        
        # Full scan
        # result = scanner.full_scan("192.168.1.1")
        
    except NmapNotInstalledError as e:
        print(f"Error: {e}")
        print("Please install Nmap from https://nmap.org/")
    except Exception as e:
        print(f"Scan failed: {e}")
