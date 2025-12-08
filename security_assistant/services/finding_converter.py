"""
Finding Converter for Security Scanners.

Converts scanner-specific findings to unified format.
"""

import hashlib
import logging
from typing import List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ScannerType(str, Enum):
    """Available scanner types."""
    BANDIT = "bandit"
    SEMGREP = "semgrep"
    TRIVY = "trivy"


class FindingSeverity(str, Enum):
    """Unified severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingConverter:
    """
    Converts findings from various scanners to unified format.
    
    Supports:
    - Bandit (Python security scanner)
    - Semgrep (multi-language SAST)
    - Trivy (container/dependency scanner)
    
    Example:
        >>> converter = FindingConverter()
        >>> unified = converter.convert_all(scanner_results)
    """
    
    # Severity mappings for each scanner
    BANDIT_SEVERITY_MAP = {
        "HIGH": FindingSeverity.HIGH,
        "MEDIUM": FindingSeverity.MEDIUM,
        "LOW": FindingSeverity.LOW,
    }
    
    SEMGREP_SEVERITY_MAP = {
        "ERROR": FindingSeverity.HIGH,
        "WARNING": FindingSeverity.MEDIUM,
        "INFO": FindingSeverity.LOW,
    }
    
    TRIVY_SEVERITY_MAP = {
        "CRITICAL": FindingSeverity.CRITICAL,
        "HIGH": FindingSeverity.HIGH,
        "MEDIUM": FindingSeverity.MEDIUM,
        "LOW": FindingSeverity.LOW,
        "UNKNOWN": FindingSeverity.INFO,
    }
    
    def __init__(self):
        """Initialize finding converter."""
        logger.debug("FindingConverter initialized")
    
    def convert_all(
        self,
        scanner_results: Dict[ScannerType, Any],
        unified_finding_class
    ) -> List:
        """
        Convert all scanner results to unified findings.
        
        Args:
            scanner_results: Dict of scanner type to scan result
            unified_finding_class: UnifiedFinding class to use
            
        Returns:
            List of unified findings
        """
        all_findings = []
        
        for scanner_type, result in scanner_results.items():
            if result is None:
                continue
            
            try:
                if scanner_type == ScannerType.BANDIT:
                    findings = self.convert_bandit(result, unified_finding_class)
                elif scanner_type == ScannerType.SEMGREP:
                    findings = self.convert_semgrep(result, unified_finding_class)
                elif scanner_type == ScannerType.TRIVY:
                    findings = self.convert_trivy(result, unified_finding_class)
                else:
                    logger.warning(f"Unknown scanner type: {scanner_type}")
                    continue
                
                all_findings.extend(findings)
                logger.debug(f"Converted {len(findings)} findings from {scanner_type.value}")
                
            except Exception as e:
                logger.error(f"Error converting {scanner_type.value} findings: {e}")
        
        return all_findings
    
    def convert_bandit(self, result, unified_finding_class) -> List:
        """Convert Bandit findings to unified format."""
        unified = []
        
        for finding in result.findings:
            finding_id = f"bandit-{finding.test_id}-{self._hash_location(finding.filename, finding.line_number)}"
            
            # Calculate line_end (handle missing line_range attribute)
            line_range = getattr(finding, 'line_range', 1)
            line_end = finding.line_number + line_range - 1 if line_range > 1 else finding.line_number
            
            # Handle CWE IDs (may be single value or list)
            cwe_ids = []
            if hasattr(finding, 'cwe_ids'):
                cwe_ids = finding.cwe_ids if isinstance(finding.cwe_ids, list) else [finding.cwe_ids]
            elif hasattr(finding, 'cwe_id') and finding.cwe_id:
                cwe_ids = [finding.cwe_id]
            
            unified_finding = unified_finding_class(
                finding_id=finding_id,
                scanner=ScannerType.BANDIT,
                severity=self.BANDIT_SEVERITY_MAP.get(finding.severity, FindingSeverity.MEDIUM),
                category="security",
                file_path=finding.filename,
                line_start=finding.line_number,
                line_end=line_end,
                title=finding.test_name,
                description=finding.issue_text,
                code_snippet=finding.code,
                cwe_ids=cwe_ids,
                confidence=finding.confidence,
                raw_data={"bandit_finding": finding}
            )
            
            unified.append(unified_finding)
        
        return unified
    
    def convert_semgrep(self, result, unified_finding_class) -> List:
        """Convert Semgrep findings to unified format."""
        unified = []
        
        for finding in result.findings:
            finding_id = f"semgrep-{finding.check_id}-{self._hash_location(finding.path, finding.start_line)}"
            
            # Get code snippet (may be 'lines' or 'code' attribute)
            code_snippet = getattr(finding, 'lines', None) or getattr(finding, 'code', '')
            
            # Get fix guidance from metadata or direct attribute
            fix_guidance = None
            if hasattr(finding, 'fix'):
                fix_guidance = finding.fix
            elif hasattr(finding, 'metadata') and isinstance(finding.metadata, dict):
                fix_guidance = finding.metadata.get('fix')
            
            # Get references from metadata or direct attribute
            references = getattr(finding, 'references', [])
            if not references and hasattr(finding, 'metadata') and isinstance(finding.metadata, dict):
                references = finding.metadata.get('references', [])
            
            unified_finding = unified_finding_class(
                finding_id=finding_id,
                scanner=ScannerType.SEMGREP,
                severity=self.SEMGREP_SEVERITY_MAP.get(finding.severity, FindingSeverity.MEDIUM),
                category=finding.category,
                file_path=finding.path,
                line_start=finding.start_line,
                line_end=finding.end_line,
                title=finding.check_id.split(".")[-1].replace("-", " ").title(),
                description=finding.message,
                code_snippet=code_snippet,
                cwe_ids=finding.cwe_ids,
                owasp_categories=finding.owasp_categories,
                references=references,
                fix_guidance=fix_guidance,
                raw_data={"semgrep_finding": finding}
            )
            
            unified.append(unified_finding)
        
        return unified
    
    def convert_trivy(self, result, unified_finding_class) -> List:
        """Convert Trivy findings to unified format."""
        unified = []
        
        for finding in result.findings:
            # Build finding ID
            vuln_id = finding.vulnerability_id or finding.secret_id or finding.misconfig_id or "unknown"
            finding_id = f"trivy-{vuln_id}-{self._hash_location(finding.target, getattr(finding, 'line', 0))}"
            
            # Build description (handle optional attributes)
            description_parts = [finding.description or finding.title]
            if hasattr(finding, 'severity_source') and finding.severity_source:
                description_parts.append(f"Source: {finding.severity_source}")
            if hasattr(finding, 'published_date') and finding.published_date:
                description_parts.append(f"Published: {finding.published_date}")
            
            # Get CWE IDs (handle optional attribute)
            cwe_ids = getattr(finding, 'cwe_ids', []) or []
            
            # Get category/finding_type (handle different attribute names and pkg_type)
            category = getattr(finding, 'finding_type', None)
            if not category:
                # Check pkg_type for secrets/misconfigs
                pkg_type = getattr(finding, 'pkg_type', None)
                if pkg_type == 'secret':
                    category = 'secret'
                elif pkg_type == 'misconfig':
                    category = 'misconfig'
                else:
                    category = getattr(finding, 'category', 'vulnerability')
            
            unified_finding = unified_finding_class(
                finding_id=finding_id,
                scanner=ScannerType.TRIVY,
                severity=self.TRIVY_SEVERITY_MAP.get(finding.severity, FindingSeverity.MEDIUM),
                category=category,
                file_path=finding.target,
                line_start=getattr(finding, 'line', 0),
                line_end=getattr(finding, 'line', 0),
                title=finding.title,
                description="\n".join(description_parts),
                code_snippet=finding.match if hasattr(finding, 'match') else "",
                cwe_ids=cwe_ids,
                references=finding.references or [],
                fix_available=bool(finding.fixed_version),
                fix_version=finding.fixed_version,
                fix_guidance=finding.resolution,
                raw_data={"trivy_finding": finding}
            )
            
            unified.append(unified_finding)
        
        return unified
    
    def _hash_location(self, file_path: str, line: int) -> str:
        """Generate short hash for location."""
        content = f"{file_path}:{line}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
