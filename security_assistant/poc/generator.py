"""
PoC Generator Engine.

Handles template loading and PoC generation based on finding types.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, Template

from security_assistant.poc.safety_checker import SafetyChecker
if TYPE_CHECKING:
    from security_assistant.orchestrator import UnifiedFinding
    from security_assistant.poc.enhancers.llm_enhancer import LLMEnhancer

logger = logging.getLogger(__name__)


class PoCError(Exception):
    """Base exception for PoC generation errors."""
    pass


class PoCGenerator:
    """
    Generates Proof-of-Concept code for security findings.
    
    Mapping strategy:
    - SQL Injection -> sqli.py
    - XSS -> xss.html
    - Command Injection -> cmdi.py
    """

    TEMPLATES_DIR = Path(__file__).parent / "templates"

    # Mapping from finding categories/titles to template names
    TEMPLATE_MAP = {
        "sql_injection": "sqli.py.j2",
        "sqli": "sqli.py.j2",
        "xss": "xss.html.j2",
        "cross_site_scripting": "xss.html.j2",
        "command_injection": "cmdi.py.j2",
        "remote_code_execution": "cmdi.py.j2",
        "path_traversal": "traversal.py.j2",
    }

    def __init__(self, llm_enhancer: Optional["LLMEnhancer"] = None):
        """
        Initialize the generator.
        
        Args:
            llm_enhancer: Optional LLM enhancer for smart generation
        """
        if not self.TEMPLATES_DIR.exists():
            raise PoCError(f"Templates directory not found: {self.TEMPLATES_DIR}")
            
        self.env = Environment(
            loader=FileSystemLoader(str(self.TEMPLATES_DIR)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.llm_enhancer = llm_enhancer
        self.safety_checker = SafetyChecker()

    def _get_template_name(self, finding: "UnifiedFinding") -> Optional[str]:
        """Determine which template to use for a finding."""
        # Check specific mapping first
        key = finding.title.lower().replace(" ", "_")
        
        # Try exact matches
        for map_key, template in self.TEMPLATE_MAP.items():
            if map_key in key:
                return template
                
        # Try category fallback
        category = finding.category.lower() if finding.category else ""
        if "injection" in category and "sql" in key:
            return "sqli.py.j2"
        if "xss" in category or "scripting" in category:
            return "xss.html.j2"
            
        return None

    async def generate(self, finding: "UnifiedFinding", output_path: Optional[str] = None) -> str:
        """
        Generate a PoC for the given finding.
        
        Args:
            finding: The security finding
            output_path: Optional path to save the generated PoC
            
        Returns:
            The generated PoC code
            
        Raises:
            PoCError: If generation fails or no template is found
        """
        template_name = self._get_template_name(finding)
        
        if not template_name:
            raise PoCError(f"No suitable PoC template found for finding type: {finding.title}")

        try:
            template = self.env.get_template(template_name)
            
            # Context defaults
            context = {
                "finding": finding,
                "target_url": "http://localhost:8000",
                "param_name": "id",
                "payload": "TEST_PAYLOAD",
            }
            
            # Enhance with LLM if available
            if self.llm_enhancer:
                enhanced_ctx = await self.llm_enhancer.enhance(finding)
                
                # Sanitize payload before using
                safe_payload = self.safety_checker.sanitize_payload(enhanced_ctx.payload)
                
                context.update({
                    "target_url": enhanced_ctx.target_url,
                    "param_name": enhanced_ctx.param_name,
                    "payload": safe_payload,
                })
            
            poc_code = template.render(**context)
            
            # Validate generated code
            self.safety_checker.validate(poc_code)
            
            if output_path:
                output_file = Path(output_path)
                output_file.write_text(poc_code, encoding="utf-8")
                logger.info(f"PoC saved to {output_file}")
                
            return poc_code
            
        except Exception as e:
            raise PoCError(f"Failed to generate PoC: {e}") from e
