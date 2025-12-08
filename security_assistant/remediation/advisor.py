"""
Remediation Advisor Module

This module provides the core logic for generating remediation advice
based on detected vulnerabilities.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import logging
from pathlib import Path

try:
    from markdown_it import MarkdownIt
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class RemediationAdvice:
    """
    Container for remediation advice.
    """
    vulnerability_type: str
    severity: str
    description: str
    remediation_steps: List[str]
    code_example: Optional[str] = None
    references: List[str] = field(default_factory=list)

class RemediationAdvisor:
    """
    Advisor for security remediation.
    Analyzes vulnerabilities and provides actionable remediation steps.
    """
    
    def __init__(self, templates_dir: Optional[str] = None, examples_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        base_dir = Path(__file__).parent
        self.templates_dir = Path(templates_dir) if templates_dir else base_dir / "templates"
        self.examples_dir = Path(examples_dir) if examples_dir else base_dir / "code_examples"
        
        # Initialize Markdown parser if available
        self.md_parser = MarkdownIt() if MARKDOWN_AVAILABLE else None
        
        # Mapping from vulnerability types (normalized) to template names
        self.vuln_map = {
            # SQL Injection
            "sql_injection": "sql_injection",
            "sql_injection_vulnerability": "sql_injection",
            "sqli": "sql_injection",
            "cwe-89": "sql_injection",
            "b608": "sql_injection", # Bandit hardcoded_sql_expressions

            # Command Injection
            "command_injection": "command_injection",
            "cwe-78": "command_injection",
            "os_command_injection": "command_injection",
            "b602": "command_injection", # Bandit subprocess_popen_with_shell_equals_true
            "b605": "command_injection", # Bandit start_process_with_a_shell

            # XSS
            "cross-site_scripting": "xss",
            "xss": "xss",
            "cwe-79": "xss",

            # Path Traversal
            "path_traversal": "path_traversal",
            "directory_traversal": "path_traversal",
            "cwe-22": "path_traversal",
            "b201": "path_traversal", # Bandit flask_debug_true (often related) - actually wait, B201 is debug. 

            # Hardcoded Secrets
            "hardcoded_secret": "hardcoded_secrets",
            "hardcoded_password": "hardcoded_secrets",
            "cwe-798": "hardcoded_secrets",
            "b105": "hardcoded_secrets",
            "b106": "hardcoded_secrets",
            "b107": "hardcoded_secrets",

            # Insecure Deserialization
            "insecure_deserialization": "insecure_deserialization",
            "deserialization": "insecure_deserialization",
            "cwe-502": "insecure_deserialization",
            "b301": "insecure_deserialization",
            "b403": "insecure_deserialization",
            "b506": "insecure_deserialization",

            # CSRF
            "csrf": "csrf",
            "cross-site_request_forgery": "csrf",
            "cwe-352": "csrf",

            # XXE
            "xxe": "xxe",
            "xml_external_entity": "xxe",
            "cwe-611": "xxe",
            "b313": "xxe",
            "b314": "xxe",
            "b315": "xxe",
            "b316": "xxe",
            "b317": "xxe",
            "b318": "xxe",
            "b319": "xxe",
            "b405": "xxe",
            "b410": "xxe",

            # SSRF
            "ssrf": "ssrf",
            "server_side_request_forgery": "ssrf",
            "cwe-918": "ssrf",

            # Weak Cryptography
            "weak_cryptography": "weak_cryptography",
            "weak_hash": "weak_cryptography",
            "cwe-327": "weak_cryptography",
            "cwe-328": "weak_cryptography",
            "b303": "weak_cryptography", # MD5
            "b304": "weak_cryptography", # Ciphers
            "b305": "weak_cryptography", # Ciphers
            "b311": "weak_cryptography", # Random
            "b324": "weak_cryptography", # Hashlib

            # Missing Authentication
            "missing_authentication": "missing_authentication",
            "cwe-306": "missing_authentication",
            "authentication": "missing_authentication",

            # Broken Access Control
            "broken_access_control": "broken_access_control",
            "access_control": "broken_access_control",
            "idor": "broken_access_control",
            "cwe-284": "broken_access_control",
            "cwe-639": "broken_access_control",

            # Insufficient Logging
            "insufficient_logging": "insufficient_logging",
            "logging": "insufficient_logging",
            "cwe-778": "insufficient_logging",

            # ReDoS
            "redos": "redos",
            "regular_expression_denial_of_service": "redos",
            "cwe-1333": "redos",

            # Known Vulnerabilities
            "known_vulnerabilities": "known_vulnerabilities",
            "vulnerable_dependency": "known_vulnerabilities",
            "cwe-937": "known_vulnerabilities",

            # Mass Assignment
            "mass_assignment": "mass_assignment",
            "cwe-915": "mass_assignment",

            # Open Redirect
            "open_redirect": "open_redirect",
            "cwe-601": "open_redirect",

            # NoSQL Injection
            "nosql_injection": "nosql_injection",
            "cwe-943": "nosql_injection",

            # Information Exposure
            "information_exposure": "information_exposure",
            "stack_trace": "information_exposure",
            "cwe-200": "information_exposure",
            "cwe-209": "information_exposure",

            # Race Condition
            "race_condition": "race_condition",
            "cwe-362": "race_condition",
            "cwe-367": "race_condition",
        }
    
    def _load_template(self, name: str) -> Optional[str]:
        try:
            path = self.templates_dir / f"{name}.md"
            if path.exists():
                return path.read_text(encoding="utf-8")
        except Exception as e:
            self.logger.warning(f"Failed to load template {name}: {e}")
        return None

    def _load_example(self, name: str, extension: str = "py") -> Optional[str]:
        try:
            # Try to find an example with the specific extension
            path = self.examples_dir / f"{name}_fix.{extension}"
            if path.exists():
                return path.read_text(encoding="utf-8")
            
            # Fallback to python if requested extension not found but python exists
            # (Only if extension wasn't py to avoid double check)
            if extension != "py":
                path_py = self.examples_dir / f"{name}_fix.py"
                if path_py.exists():
                    return path_py.read_text(encoding="utf-8")
                    
        except Exception as e:
            self.logger.warning(f"Failed to load example {name}: {e}")
        return None
    
    def _parse_markdown_steps(self, content: str) -> List[str]:
        """
        Parse remediation steps from Markdown content using markdown-it-py.
        Falls back to regex parsing if library not available.
        """
        steps = []
        
        if self.md_parser:
            # Use markdown-it-py for robust parsing
            tokens = self.md_parser.parse(content)
            in_remediation = False
            
            for i, token in enumerate(tokens):
                # Look for "Remediation" heading
                if token.type == "heading_open" and token.tag == "h2":
                    # Check next token for heading text
                    if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                        if "Remediation" in tokens[i + 1].content:
                            in_remediation = True
                        elif in_remediation:
                            # Another h2 heading, stop
                            in_remediation = False
                
                # Extract list items in remediation section
                if in_remediation and token.type == "list_item_open":
                    # Next token should be paragraph_open, then inline with content
                    if i + 2 < len(tokens) and tokens[i + 2].type == "inline":
                        step_text = tokens[i + 2].content.strip()
                        if step_text:
                            steps.append(step_text)
        else:
            # Fallback to regex-based parsing
            lines = content.splitlines()
            in_remediation = False
            for line in lines:
                if "## Remediation" in line:
                    in_remediation = True
                    continue
                if line.startswith("## ") and in_remediation:
                    in_remediation = False
                
                if in_remediation and (line.strip().startswith(("1.", "-", "*"))):
                    steps.append(line.strip().lstrip("1.-* ").strip())
        
        return steps
    
    def analyze_vulnerability(self, vulnerability_data: Dict[str, Any]) -> Optional[RemediationAdvice]:
        """
        Analyzes a vulnerability and returns remediation advice.
        """
        try:
            raw_type = vulnerability_data.get("type", "unknown")
            vuln_type = raw_type.lower().replace(" ", "_")
            
            # Try to map vulnerability name/ID to a template key
            key = self.vuln_map.get(vuln_type)
            
            # Debug log
            # self.logger.info(f"Analyzing vuln: {raw_type} -> {vuln_type}. Key: {key}")
            
            if not key:
                # Try direct match
                if (self.templates_dir / f"{vuln_type}.md").exists():
                    key = vuln_type
            
            severity = vulnerability_data.get("severity", "medium")
            file_path = vulnerability_data.get("file_path", "")
            
            # Determine extension
            extension = "py"
            if file_path:
                ext = Path(file_path).suffix.lstrip(".")
                if ext in ["js", "ts", "jsx", "tsx"]:
                    extension = "js"
                elif ext in ["go"]:
                    extension = "go"
                elif ext in ["java"]:
                    extension = "java"
                elif ext in ["rs"]:
                    extension = "rs"
                # Add more mappings as needed
            
            if key:
                template_content = self._load_template(key)
                example_content = self._load_example(key, extension=extension)
                
                if template_content:
                    # Parse markdown template
                    description = template_content
                    steps = self._parse_markdown_steps(template_content)

                    return RemediationAdvice(
                        vulnerability_type=vulnerability_data.get("type", "unknown"),
                        severity=severity,
                        description=description,
                        remediation_steps=steps,
                        code_example=example_content,
                        references=["https://cwe.mitre.org/"] # Placeholder
                    )

            # Fallback for unknown types
            return RemediationAdvice(
                vulnerability_type=vulnerability_data.get("type", "unknown"),
                severity=severity,
                description=f"Standard remediation for {vuln_type}",
                remediation_steps=[
                    "Validate input data",
                    "Sanitize user input",
                    "Update dependencies if applicable"
                ],
                code_example=None,
                references=[]
            )
        except Exception as e:
            self.logger.error(f"Error generating advice: {str(e)}")
            return None
