"""
Issue Converter for GitLab Integration.

Converts security findings to GitLab issues with rich formatting.
"""

import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class IssueConverter:
    """
    Converts security findings to GitLab issues.
    
    Features:
    - Rich markdown formatting
    - Severity-based emojis
    - CWE and OWASP links
    - Code snippets
    - Fix guidance
    - Priority-based filtering
    
    Example:
        >>> converter = IssueConverter()
        >>> issues = converter.convert_result(result, "MyProject", top_n=20)
    """
    
    def __init__(self):
        """Initialize issue converter."""
        logger.debug("IssueConverter initialized")
    
    def convert_result(
        self,
        result,
        project_name: str,
        top_n: Optional[int] = None,
    ) -> List:
        """
        Convert orchestration result to GitLab issues.
        
        Args:
            result: OrchestrationResult to convert
            project_name: GitLab project name
            top_n: Only create issues for top N priority findings (default: all)
        
        Returns:
            List of IssueData ready for GitLab
        
        Example:
            >>> result = orchestrator.scan_directory("src/")
            >>> issues = converter.convert_result(result, "MyProject", top_n=20)
        """
        findings = result.deduplicated_findings
        
        # Filter to top N if specified
        if top_n:
            findings = sorted(findings, key=lambda f: f.priority_score, reverse=True)[:top_n]
            logger.info(f"Converting top {top_n} findings to GitLab issues")
        else:
            logger.info(f"Converting {len(findings)} findings to GitLab issues")
        
        issues = []
        for finding in findings:
            issue = self.convert_finding(finding, project_name)
            issues.append(issue)
        
        return issues
    
    def convert_finding(self, finding, project_name: str):
        """
        Convert a unified finding to GitLab issue.
        
        Args:
            finding: UnifiedFinding to convert
            project_name: GitLab project name
            
        Returns:
            IssueData object
        """
        # Import here to avoid circular dependency
        from ..gitlab_api import IssueData
        
        # Build title
        file_name = Path(finding.file_path).name
        title = f"{finding.severity_emoji} {finding.title} in {file_name}"
        
        # Build description
        description = self._build_description(finding)
        
        # Determine labels
        labels = self._build_labels(finding)
        
        return IssueData(
            title=title,
            description=description,
            labels=labels,
            confidential=True
        )
    
    def _build_description(self, finding) -> str:
        """Build rich markdown description for GitLab issue."""
        description_parts = [
            f"## {finding.severity_emoji} Security Finding",
            "",
            f"**Severity:** {finding.severity.value}",
            f"**Category:** {finding.category}",
            f"**Scanner:** {finding.scanner.value}",
            f"**Priority Score:** {finding.priority_score:.1f}/100",
        ]
        
        # Add confidence if available
        if finding.confidence:
            description_parts.append(f"**Confidence:** {finding.confidence}")
        
        # Add enrichment info
        if finding.is_active_exploit:
            description_parts.append("**⚠️ ACTIVE EXPLOIT (KEV):** This vulnerability is actively exploited in the wild!")
        
        if finding.is_false_positive:
            description_parts.append(f"**🤔 Possible False Positive:** Confidence {finding.fp_confidence:.0%}")
            if finding.fp_reasons:
                description_parts.append(f"  - Reasons: {', '.join(finding.fp_reasons)}")
        
        if finding.is_reachable is False:
            description_parts.append(f"**📦 Unreachable Dependency:** Confidence {finding.reachability_confidence:.0%}")
        
        # Location section
        description_parts.extend([
            "",
            "### Location",
            f"**File:** `{finding.file_path}`",
            f"**Lines:** {finding.line_start}-{finding.line_end}",
            "",
            "### Description",
            finding.description,
        ])
        
        # Add code snippet if available
        if finding.code_snippet:
            description_parts.extend([
                "",
                "### Code",
                "```",
                finding.code_snippet,
                "```",
            ])
        
        # Add CWE links
        if finding.cwe_ids:
            cwe_links = [
                f"[{cwe}](https://cwe.mitre.org/data/definitions/{cwe.replace('CWE-', '')}.html)"
                for cwe in finding.cwe_ids
            ]
            description_parts.extend([
                "",
                f"**CWE:** {', '.join(cwe_links)}"
            ])
        
        # Add OWASP categories
        if finding.owasp_categories:
            description_parts.extend([
                "",
                f"**OWASP:** {', '.join(finding.owasp_categories)}"
            ])
        
        # Add ML scoring info
        if finding.ml_score is not None:
            description_parts.extend([
                "",
                "### ML Analysis",
                f"**ML Score:** {finding.ml_score:.1f}/100",
            ])
            if finding.epss_score is not None:
                description_parts.append(f"**EPSS Score:** {finding.epss_score:.2%} (exploit probability)")
        
        # Add fix information
        if finding.fix_available:
            description_parts.extend([
                "",
                "### Fix Available ✅",
            ])
            if finding.fix_version:
                description_parts.append(f"**Version:** {finding.fix_version}")
            if finding.fix_guidance:
                description_parts.append(f"\n{finding.fix_guidance}")
        
        # Add references
        if finding.references:
            description_parts.extend([
                "",
                "### References",
                *[f"- {ref}" for ref in finding.references[:5]],
            ])
        
        # Add footer
        description_parts.extend([
            "",
            "---",
            f"*Detected by {finding.scanner.value} scanner*",
            f"*Finding ID: `{finding.finding_id}`*"
        ])
        
        return "\n".join(description_parts)
    
    def _build_labels(self, finding) -> List[str]:
        """Build labels for GitLab issue."""
        labels = [
            "security",
            finding.scanner.value,
            finding.category,
            f"severity::{finding.severity.value.lower()}",
        ]
        
        # Add critical label for high-severity findings
        if finding.severity.value in ["CRITICAL", "HIGH"]:
            labels.append("critical")
        
        # Add fix-available label
        if finding.fix_available:
            labels.append("fix-available")
        
        # Add KEV label for active exploits
        if finding.is_active_exploit:
            labels.append("kev")
            labels.append("active-exploit")
        
        # Add false-positive label
        if finding.is_false_positive:
            labels.append("possible-fp")
        
        # Add unreachable label
        if finding.is_reachable is False:
            labels.append("unreachable")
        
        return labels
