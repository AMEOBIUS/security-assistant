"""
SQLMap Scanner Integration

Offensive security scanner for automated SQL injection detection and exploitation using SQLMap.

Features:
- SQL injection detection (GET/POST parameters)
- Database fingerprinting
- Data extraction
- Blind SQLi techniques
- JSON/XML output parsing
- Integration with authorization system

Requirements:
- SQLMap must be installed on the system
- Python 3.11+

Example usage:
    scanner = SQLMapScanner()
    result = scanner.scan("http://example.com/login.php?id=1", params="id")
"""

import json
import logging
from typing import Dict, List, Optional, Union

from security_assistant.common.executor import CommandExecutionError, CommandExecutor
from security_assistant.offensive.base_offensive_scanner import OffensiveScanner

logger = logging.getLogger(__name__)


class SQLMapScannerError(Exception):
    """Base exception for SQLMap scanner errors."""
    pass


class SQLMapNotInstalledError(SQLMapScannerError):
    """SQLMap is not installed on the system."""
    pass


class SQLMapScanFailedError(SQLMapScannerError):
    """SQLMap scan failed to execute."""
    pass


class SQLMapScanner(OffensiveScanner):
    """
    SQLMap security scanner for SQL injection detection and exploitation.
    
    Inherits from OffensiveScanner for authorization and ToS enforcement.
    """
    
    def __init__(self):
        """Initialize SQLMap scanner."""
        super().__init__()
        self._check_sqlmap_installation()
    
    @property
    def scanner_type(self) -> str:
        """Type of offensive scanner."""
        return "web"
    
    @property
    def risk_level(self) -> str:
        """Risk level of scanner."""
        return "HIGH"
    
    def _check_sqlmap_installation(self):
        """Check if SQLMap is installed on the system."""
        try:
            result = CommandExecutor.run(
                ["sqlmap", "--version"],
                timeout=5,
                check=True
            )
            
            logger.info(f"SQLMap installed: {result.stdout.strip()}")
            
        except (CommandExecutionError, FileNotFoundError):
            raise SQLMapNotInstalledError(
                "SQLMap is not installed. Please install SQLMap from https://sqlmap.org/ "
                "and ensure it's in your PATH."
            )
    
    def scan(
        self,
        target: str,
        params: Optional[Union[str, List[str]]] = None,
        data: Optional[str] = None,
        level: int = 1,
        risk: int = 1,
        batch: bool = False,
        output_format: str = "json",
        **kwargs
    ) -> Dict:
        """
        Perform SQLMap scan on target.
        
        Args:
            target: Target URL
            params: GET parameters to test (e.g., "id" or ["id", "page"])
            data: POST data to test (e.g., "username=admin&password=test")
            level: Test level (1-5, where 1 is basic, 5 is exhaustive)
            risk: Risk level (1-3, where 1 is safe, 3 is risky)
            batch: Run in batch mode (non-interactive)
            output_format: Output format (json, xml, csv)
            **kwargs: Additional SQLMap arguments
            
        Returns:
            Dictionary with scan results
            
        Raises:
            TargetNotAuthorizedError: If target not authorized
            SQLMapScannerError: If scan fails
        """
        # Check authorization
        self._check_authorization(target, "web")
        
        # Build SQLMap command
        cmd = self._build_sqlmap_command(
            target,
            params=params,
            data=data,
            level=level,
            risk=risk,
            batch=batch,
            output_format=output_format,
            **kwargs
        )
        
        # Log offensive action
        self._log_offensive_action("sqlmap_scan", target, f"Command: {' '.join(cmd)}")
        
        try:
            # Execute SQLMap
            result = CommandExecutor.run(
                cmd,
                timeout=600,
                check=True
            )
            
            # Parse output
            if output_format == "json":
                scan_result = self._parse_json_output(result.stdout)
            elif output_format == "xml":
                scan_result = self._parse_xml_output(result.stdout)
            else:
                scan_result = {"raw_output": result.stdout}
            
            # Standardize result
            return self._standardize_result(scan_result)
            
        except CommandExecutionError as e:
            raise SQLMapScanFailedError(f"SQLMap scan failed: {e}") from e
        except Exception as e:
            raise SQLMapScanFailedError(f"SQLMap scan failed: {e}") from e
    
    def _build_sqlmap_command(
        self,
        target: str,
        params: Optional[Union[str, List[str]]] = None,
        data: Optional[str] = None,
        level: int = 1,
        risk: int = 1,
        batch: bool = False,
        output_format: str = "json",
        **kwargs
    ) -> List[str]:
        """
        Build SQLMap command line.
        
        Args:
            target: Target URL
            params: GET parameters to test
            data: POST data to test
            level: Test level
            risk: Risk level
            batch: Batch mode
            output_format: Output format
            **kwargs: Additional arguments
            
        Returns:
            List of command arguments
        """
        cmd = ["sqlmap"]
        
        # Add target URL
        cmd.extend(["-u", target])
        
        # Add parameters if specified
        if params:
            if isinstance(params, list):
                for param in params:
                    cmd.extend(["-p", param])
            else:
                cmd.extend(["-p", params])
        
        # Add POST data if specified
        if data:
            cmd.extend(["--data", data])
        
        # Add level
        cmd.extend(["--level", str(level)])
        
        # Add risk
        cmd.extend(["--risk", str(risk)])
        
        # Add batch mode
        if batch:
            cmd.append("--batch")
        
        # Add output format
        if output_format == "json":
            cmd.extend(["--output-dir", ".sqlmap/output", "--json"])
        elif output_format == "xml":
            cmd.extend(["--output-dir", ".sqlmap/output", "--xml"])
        
        # Add additional kwargs
        for key, value in kwargs.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f"--{key}")
            else:
                cmd.extend([f"--{key}", str(value)])
        
        return cmd
    
    def _parse_json_output(self, json_output: str) -> Dict:
        """
        Parse SQLMap JSON output.
        
        Args:
            json_output: JSON output from SQLMap
            
        Returns:
            Dictionary with parsed results
            
        Raises:
            SQLMapScannerError: If JSON parsing fails
        """
        try:
            return json.loads(json_output)
        except json.JSONDecodeError as e:
            raise SQLMapScannerError(f"Failed to parse SQLMap JSON output: {str(e)}")  # noqa: B904
    
    def _parse_xml_output(self, xml_output: str) -> Dict:
        """
        Parse SQLMap XML output (placeholder for future implementation).
        
        Args:
            xml_output: XML output from SQLMap
            
        Returns:
            Dictionary with parsed results
        """
        # TODO: Implement XML parsing
        return {"raw_xml": xml_output}
    
    def _standardize_result(self, raw_result: Dict) -> Dict:
        """
        Standardize SQLMap result format.
        
        Args:
            raw_result: Raw SQLMap output
            
        Returns:
            Standardized result dictionary
        """
        result = {
            "scanner": "sqlmap",
            "target": raw_result.get("target", "unknown"),
            "status": "completed",
            "vulnerabilities": [],
            "timestamp": self._get_current_timestamp()
        }
        
        # Extract vulnerabilities from raw result
        if "vulnerabilities" in raw_result:
            for vuln in raw_result["vulnerabilities"]:
                result["vulnerabilities"].append({
                    "type": vuln.get("type", "sql_injection"),
                    "parameter": vuln.get("parameter", "unknown"),
                    "severity": vuln.get("severity", "HIGH"),
                    "description": vuln.get("description", ""),
                    "payload": vuln.get("payload", "")
                })
        
        return result
    
    def quick_scan(self, target: str, params: Optional[str] = None) -> Dict:
        """
        Perform quick SQLMap scan (level 1, risk 1).
        
        Args:
            target: Target URL
            params: GET parameters to test
            
        Returns:
            Scan results
        """
        return self.scan(
            target=target,
            params=params,
            level=1,
            risk=1,
            batch=True,
            output_format="json"
        )
    
    def full_scan(self, target: str, params: Optional[str] = None) -> Dict:
        """
        Perform full SQLMap scan (level 5, risk 3).
        
        Args:
            target: Target URL
            params: GET parameters to test
            
        Returns:
            Scan results
        """
        return self.scan(
            target=target,
            params=params,
            level=5,
            risk=3,
            batch=True,
            output_format="json"
        )
