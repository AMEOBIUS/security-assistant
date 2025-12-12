"""
Fix Generator Service.

Uses LLM to generate code fixes for security findings.
"""

import logging
from pathlib import Path
from typing import Tuple

from security_assistant.orchestrator import UnifiedFinding
from security_assistant.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class FixStrategy:
    """Fix generation strategies."""
    SAFE = "safe"           # Conservative, minimal changes
    AGGRESSIVE = "aggressive"  # Complete refactor if needed
    MINIMAL = "minimal"     # Smallest possible change


class FixGenerator:
    """Generate code fixes using LLM."""
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize fix generator.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm_service = llm_service
    
    async def generate_fix(
        self, 
        finding: UnifiedFinding,
        strategy: str = FixStrategy.SAFE
    ) -> Tuple[str, str]:
        """
        Generate fix for a finding.
        
        Args:
            finding: Security finding to fix
            strategy: Fix strategy (safe, aggressive, minimal)
            
        Returns:
            Tuple of (fixed_code, explanation)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If LLM response is invalid
        """
        # Read original file
        file_path = Path(finding.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        original_code = file_path.read_text(encoding='utf-8')
        
        # Generate fix using LLM
        prompt = self._build_fix_prompt(finding, original_code, strategy)
        response = await self.llm_service.client.complete(
            prompt, 
            temperature=0.2
        )
        
        # Parse response
        fixed_code, explanation = self._parse_fix_response(response.content)
        
        return fixed_code, explanation
    
    def _build_fix_prompt(
        self, 
        finding: UnifiedFinding, 
        original_code: str,
        strategy: str
    ) -> str:
        """Build prompt for fix generation."""
        
        strategy_instructions = {
            FixStrategy.SAFE: "Make minimal, conservative changes. Preserve all existing functionality.",
            FixStrategy.AGGRESSIVE: "Refactor completely if needed. Modernize code and apply best practices.",
            FixStrategy.MINIMAL: "Make the smallest possible change to fix the vulnerability."
        }
        
        return f"""You are a security expert. Fix this vulnerability in the code.

**Vulnerability:**
- Type: {finding.category}
- Severity: {finding.severity}
- Title: {finding.title}
- Description: {finding.description}
- Location: {finding.file_path}:{finding.line_start}

**Original Code:**
```
{original_code}
```

**Vulnerable Section (lines {finding.line_start}-{finding.line_end}):**
```
{finding.code_snippet or "N/A"}
```

**Fix Strategy:** {strategy}
{strategy_instructions.get(strategy, "")}

**Requirements:**
1. Fix the vulnerability completely
2. Maintain existing functionality
3. Follow best practices for {Path(finding.file_path).suffix.lstrip('.')} code
4. Add security comments explaining the fix
5. Use modern libraries/patterns where appropriate

**Output Format:**
FIXED_CODE:
```
<complete fixed file content>
```

EXPLANATION:
<brief explanation of what was changed and why (2-3 sentences)>
"""
    
    def _parse_fix_response(self, response: str) -> Tuple[str, str]:
        """
        Parse LLM response into code and explanation.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Tuple of (code, explanation)
            
        Raises:
            ValueError: If response format is invalid
        """
        # Extract code block
        code_start = response.find("FIXED_CODE:")
        code_end = response.find("EXPLANATION:")
        
        if code_start == -1 or code_end == -1:
            raise ValueError("Invalid LLM response format - missing FIXED_CODE or EXPLANATION markers")
        
        code_section = response[code_start:code_end].strip()
        explanation_section = response[code_end:].strip()
        
        # Extract code from markdown block
        code = self._extract_code_block(code_section)
        explanation = explanation_section.replace("EXPLANATION:", "").strip()
        
        if not code:
            raise ValueError("No code found in LLM response")
        
        return code, explanation
    
    def _extract_code_block(self, text: str) -> str:
        """
        Extract code from markdown code block.
        
        Args:
            text: Text containing markdown code block
            
        Returns:
            Extracted code
        """
        lines = text.split('\n')
        in_block = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('```'):
                in_block = not in_block
                continue
            if in_block:
                code_lines.append(line)
        
        return '\n'.join(code_lines)
