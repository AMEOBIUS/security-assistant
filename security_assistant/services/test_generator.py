"""
Test Generator Service.

Generates pytest tests for security fixes.
"""

import logging
from pathlib import Path
from typing import Tuple

from security_assistant.orchestrator import UnifiedFinding
from security_assistant.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class PytestTestGenerator:
    """Generate pytest tests for fixes."""
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize test generator.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm_service = llm_service
    
    async def generate_test(
        self,
        finding: UnifiedFinding,
        fixed_code: str
    ) -> Tuple[str, str]:
        """
        Generate pytest test for a fix.
        
        Args:
            finding: Security finding that was fixed
            fixed_code: The fixed code
            
        Returns:
            Tuple of (test_code, test_file_path)
        """
        # Build prompt
        prompt = self._build_test_prompt(finding, fixed_code)
        
        # Generate test using LLM
        response = await self.llm_service.client.complete(
            prompt,
            temperature=0.2
        )
        
        # Parse response
        test_code = self._parse_test_response(response.content)
        
        # Determine test file path
        test_file_path = self._get_test_file_path(finding.file_path)
        
        return test_code, test_file_path
    
    def _build_test_prompt(
        self,
        finding: UnifiedFinding,
        fixed_code: str
    ) -> str:
        """Build prompt for test generation."""
        
        return f"""You are a testing expert. Generate a pytest test for this security fix.

**Original Vulnerability:**
- Type: {finding.category}
- Severity: {finding.severity}
- Title: {finding.title}
- File: {finding.file_path}:{finding.line_start}

**Fixed Code:**
```python
{fixed_code}
```

**Requirements:**
1. Test that the vulnerability is fixed
2. Test that functionality still works
3. Test edge cases
4. Use pytest fixtures where appropriate
5. Include docstrings
6. Test both positive and negative cases

**Output Format:**
TEST_CODE:
```python
<complete pytest test code>
```
"""
    
    def _parse_test_response(self, response: str) -> str:
        """
        Parse LLM response to extract test code.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Test code
        """
        # Find TEST_CODE marker
        code_start = response.find("TEST_CODE:")
        if code_start == -1:
            raise ValueError("Invalid LLM response - missing TEST_CODE marker")
        
        code_section = response[code_start:].strip()
        
        # Extract code from markdown block
        lines = code_section.split('\n')
        in_block = False
        code_lines = []
        
        for line in lines:
            if line.strip().startswith('```'):
                in_block = not in_block
                continue
            if in_block:
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def _get_test_file_path(self, source_file: str) -> str:
        """
        Determine test file path for source file.
        
        Args:
            source_file: Path to source file
            
        Returns:
            Path to test file
        """
        source_path = Path(source_file)
        
        # Convert security_assistant/module.py -> tests/test_module.py
        if 'security_assistant' in source_file:
            test_name = f"test_{source_path.stem}.py"
            return f"tests/{test_name}"
        
        # For other files, put in tests/
        test_name = f"test_{source_path.stem}.py"
        return f"tests/{test_name}"
