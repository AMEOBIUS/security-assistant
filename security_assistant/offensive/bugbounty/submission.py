"""
Bug Bounty Submission Module

Handles vulnerability submission workflow:
- Convert findings to bug bounty reports
- Platform-specific formatting
- Evidence collection
- Report validation
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from security_assistant.offensive.authorization import AuthorizationService
from security_assistant.orchestrator import UnifiedFinding

logger = logging.getLogger(__name__)


class BugBountySubmission:
    """
    Bug bounty submission handler.
    
    Args:
        finding: UnifiedFinding to submit
        platform: Target platform (hackerone, bugcrowd)
        auth_service: Authorization service for ToS checking
    """
    
    def __init__(
        self,
        finding: UnifiedFinding,
        platform: str = "hackerone",
        auth_service: Optional[AuthorizationService] = None
    ):
        self.finding = finding
        self.platform = platform
        self.auth_service = auth_service or AuthorizationService()
        self.evidence_files = []
        
        # Validate submission
        self._validate_submission()
        
        logger.info(f"BugBountySubmission created for {finding.title} on {platform}")
    
    def _validate_submission(self) -> None:
        """Validate submission requirements."""
        if not self.auth_service.check_tos_accepted():
            raise Exception("Must accept Terms of Service before submitting to bug bounty programs")
        
        if not self.finding.file_path:
            raise ValueError("Finding must have a file path")
        
        if not self.finding.title:
            raise ValueError("Finding must have a title")
    
    def add_evidence(self, file_path: str, description: str) -> None:
        """Add evidence file to submission."""
        evidence_path = Path(file_path)
        if not evidence_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")
        
        self.evidence_files.append({
            "path": str(evidence_path),
            "description": description
        })
        
        logger.info(f"Added evidence: {file_path} ({description})")
    
    def generate_report_data(self) -> Dict[str, Any]:
        """Generate platform-specific report data."""
        if self.platform == "hackerone":
            return self._generate_hackerone_report()
        elif self.platform == "bugcrowd":
            return self._generate_bugcrowd_report()
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
    
    def _generate_hackerone_report(self) -> Dict[str, Any]:
        """Generate HackerOne report format."""
        severity_mapping = {
            "CRITICAL": "critical",
            "HIGH": "high", 
            "MEDIUM": "medium",
            "LOW": "low",
            "INFO": "informational"
        }
        
        report = {
            "title": f"[{self.finding.scanner}] {self.finding.title}",
            "vulnerability_information": self._format_vulnerability_info(),
            "severity": severity_mapping.get(self.finding.severity, "medium"),
            "steps_to_reproduce": self._format_steps_to_reproduce(),
            "attack_surface": self._format_attack_surface(),
            "impact": self._format_impact()
        }
        
        if self.finding.cwe_ids:
            report["cwe_ids"] = self.finding.cwe_ids
        
        if hasattr(self.finding, 'cvss_score') and self.finding.cvss_score:
            report["cvss_score"] = self.finding.cvss_score
        
        return report
    
    def _generate_bugcrowd_report(self) -> Dict[str, Any]:
        """Generate Bugcrowd report format."""
        severity_mapping = {
            "CRITICAL": "critical",
            "HIGH": "high", 
            "MEDIUM": "medium",
            "LOW": "low",
            "INFO": "informational"
        }
        
        report = {
            "title": f"[{self.finding.scanner}] {self.finding.title}",
            "description": self._format_vulnerability_info(),
            "severity": severity_mapping.get(self.finding.severity, "medium"),
            "steps_to_reproduce": self._format_steps_to_reproduce(),
            "vulnerability_type": self._get_vulnerability_type(),
            "impact": self._format_impact()
        }
        
        if hasattr(self.finding, 'cvss_score') and self.finding.cvss_score:
            report["cvss_score"] = self.finding.cvss_score
        
        return report
    
    def _format_vulnerability_info(self) -> str:
        """Format vulnerability information."""
        info = []
        info.append(f"# {self.finding.title}")
        info.append("")
        info.append(f"**Scanner:** {self.finding.scanner}")
        info.append(f"**Severity:** {self.finding.severity}")
        info.append(f"**File:** {self.finding.file_path}")
        info.append(f"**Lines:** {self.finding.line_start}-{self.finding.line_end}")
        
        if self.finding.cwe_ids:
            info.append(f"**CWE IDs:** {', '.join(self.finding.cwe_ids)}")
        
        if self.finding.owasp_categories:
            info.append(f"**OWASP Categories:** {', '.join(self.finding.owasp_categories)}")
        
        info.append("")
        info.append("**Description:**")
        info.append(self.finding.description)
        
        return "\n".join(info)
    
    def _format_steps_to_reproduce(self) -> str:
        """Format steps to reproduce."""
        steps = []
        steps.append("1. Locate the vulnerable code in the repository")
        steps.append(f"   - File: `{self.finding.file_path}`")
        steps.append(f"   - Lines: {self.finding.line_start}-{self.finding.line_end}")
        steps.append("")
        steps.append("2. Review the vulnerability description")
        steps.append("3. Implement the suggested fix")
        steps.append("4. Verify the fix resolves the issue")
        
        if self.finding.fix_available:
            steps.append("5. Apply the automated fix if available")
        
        return "\n".join(steps)
    
    def _format_attack_surface(self) -> str:
        """Format attack surface information."""
        return f"Source code vulnerability in {self.finding.file_path}"
    
    def _format_impact(self) -> str:
        """Format impact information."""
        impact = []
        impact.append(f"This {self.finding.category.lower()} vulnerability could allow attackers to:")
        
        if "command_injection" in self.finding.category.lower():
            impact.append("- Execute arbitrary commands on the server")
            impact.append("- Gain unauthorized access to the system")
        elif "sql_injection" in self.finding.category.lower():
            impact.append("- Access or modify database contents")
            impact.append("- Bypass authentication mechanisms")
        elif "xss" in self.finding.category.lower():
            impact.append("- Execute arbitrary JavaScript in user browsers")
            impact.append("- Steal session cookies or sensitive data")
        else:
            impact.append("- Compromise system security")
            impact.append("- Lead to unauthorized access or data breaches")
        
        return "\n".join(impact)
    
    def _get_vulnerability_type(self) -> str:
        """Get vulnerability type for Bugcrowd."""
        type_mapping = {
            "command_injection": "Command Injection",
            "sql_injection": "SQL Injection",
            "xss": "Cross-Site Scripting",
            "hardcoded_secret": "Hardcoded Secret",
            "weak_cryptography": "Weak Cryptography"
        }
        
        for pattern, vuln_type in type_mapping.items():
            if pattern in self.finding.category.lower():
                return vuln_type
        
        return "Security Vulnerability"
    
    def generate_evidence_report(self) -> str:
        """Generate evidence report."""
        if not self.evidence_files:
            return "No evidence files attached."
        
        evidence_report = []
        evidence_report.append("## Evidence Files")
        evidence_report.append("")
        
        for i, evidence in enumerate(self.evidence_files, 1):
            evidence_report.append(f"{i}. **{evidence['description']}**")
            evidence_report.append(f"   - File: `{evidence['path']}`")
            evidence_report.append("")
        
        return "\n".join(evidence_report)
    
    def create_submission_package(self, output_dir: str = "submissions") -> str:
        """Create complete submission package."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in self.finding.title if c.isalnum() or c in "_- ")[:50]
        package_name = f"submission_{timestamp}_{safe_title}.json"
        package_path = Path(output_dir) / package_name
        
        # Create output directory if it doesn't exist
        package_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate submission data
        submission_data = {
            "finding": self.finding.dict(),
            "report": self.generate_report_data(),
            "evidence": self.evidence_files,
            "metadata": {
                "platform": self.platform,
                "timestamp": datetime.now().isoformat(),
                "generated_by": "Security Assistant Bug Bounty Integration"
            }
        }
        
        # Save to file
        with open(package_path, "w") as f:
            json.dump(submission_data, f, indent=2)
        
        logger.info(f"Created submission package: {package_path}")
        return str(package_path)
