"""
SARIF Reporter Implementation

Generates SARIF (Static Analysis Results Interchange Format) reports
for integration with CI/CD systems like GitHub Advanced Security.

Version: 1.0.0
"""

import json
import logging
from typing import Any, Dict, List
from datetime import datetime

from .base_reporter import BaseReporter, ReportFormat
from ..orchestrator import FindingSeverity

logger = logging.getLogger(__name__)

class SarifReporter(BaseReporter):
    """
    Generates SARIF 2.1.0 compliant reports.
    Essential for GitHub Code Scanning and other CI/CD integrations.
    """
    
    @property
    def format(self) -> ReportFormat:
        return ReportFormat.SARIF
    
    def generate(self, result: Any, **kwargs) -> str:
        """
        Generate SARIF report.
        
        Args:
            result: OrchestrationResult
            **kwargs: Additional options
        
        Returns:
            JSON string in SARIF format
        """
        rules = []
        results = []
        rule_indices = {}
        
        # Process findings
        for finding in result.deduplicated_findings:
            # Create rule if not exists
            rule_id = finding.cwe_ids[0] if finding.cwe_ids else f"SEC-{finding.scanner.value.upper()}-001"
            
            if rule_id not in rule_indices:
                rule = {
                    "id": rule_id,
                    "name": finding.title,
                    "shortDescription": {
                        "text": finding.title
                    },
                    "fullDescription": {
                        "text": finding.description
                    },
                    "help": {
                        "text": finding.fix_guidance or "No remediation advice available.",
                        "markdown": f"{finding.description}\n\n## Remediation\n{finding.fix_guidance or 'No remediation advice available.'}"
                    },
                    "properties": {
                        "tags": [
                            "security",
                            finding.scanner.value
                        ],
                        "precision": "high" if finding.confidence >= 0.8 else "medium"
                    }
                }
                
                # Add CWE tags
                if finding.cwe_ids:
                    for cwe in finding.cwe_ids:
                        rule["properties"]["tags"].append(f"cwe-{cwe.split('-')[-1]}")
                
                rules.append(rule)
                rule_indices[rule_id] = len(rules) - 1
            
            # Map severity
            level = self._map_severity_to_sarif(finding.severity)
            
            # Create result
            sarif_result = {
                "ruleId": rule_id,
                "ruleIndex": rule_indices[rule_id],
                "level": level,
                "message": {
                    "text": finding.description
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.file_path.replace("\\", "/")
                            },
                            "region": {
                                "startLine": finding.line_start,
                                "endLine": finding.line_end if finding.line_end >= finding.line_start else finding.line_start
                            }
                        }
                    }
                ]
            }
            
            # Add code snippet if available
            if self.include_code_snippets and finding.code_snippet:
                sarif_result["locations"][0]["physicalLocation"]["contextRegion"] = {
                    "startLine": finding.line_start,
                    "snippet": {
                        "text": finding.code_snippet
                    }
                }
            
            results.append(sarif_result)
            
        # Construct full SARIF object
        sarif_report = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Security Assistant",
                            "version": "2.0.0",
                            "informationUri": "https://github.com/your-org/security-assistant",
                            "rules": rules
                        }
                    },
                    "results": results,
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "endTimeUtc": result.scan_time.isoformat() if result.scan_time else datetime.utcnow().isoformat()
                        }
                    ]
                }
            ]
        }
        
        return json.dumps(sarif_report, indent=2)

    def _map_severity_to_sarif(self, severity: FindingSeverity) -> str:
        """Map internal severity to SARIF level."""
        severity_map = {
            FindingSeverity.CRITICAL: "error",
            FindingSeverity.HIGH: "error",
            FindingSeverity.MEDIUM: "warning",
            FindingSeverity.LOW: "note",
            FindingSeverity.INFO: "note"
        }
        return severity_map.get(severity, "warning")
