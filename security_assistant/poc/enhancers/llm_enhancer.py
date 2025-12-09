"""
LLM Enhancer for PoC Generation.

Uses LLM to extract context (URLs, parameters, payloads) from vulnerable code
to make Proof-of-Concepts executable.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict

from security_assistant.orchestrator import UnifiedFinding
from security_assistant.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class EnhancedContext:
    """Context extracted by LLM."""
    target_url: str
    param_name: str
    payload: str
    method: str = "GET"
    notes: str = ""


class LLMEnhancer:
    """
    Enhances PoC generation using LLM analysis.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def enhance(self, finding: UnifiedFinding) -> EnhancedContext:
        """
        Analyze finding and extract execution context.
        """
        if not await self.llm_service.is_available():
            logger.warning("LLM not available, returning default context")
            return self._get_default_context(finding)

        prompt = self._build_prompt(finding)
        
        try:
            # We expect a JSON response
            response = await self.llm_service.client.complete(
                prompt, 
                temperature=0.1,
                response_format={"type": "json_object"}  # Optimization for OpenAI/NVIDIA
            )
            
            data = self._parse_json(response.content)
            
            return EnhancedContext(
                target_url=data.get("target_url", "http://localhost:8000"),
                param_name=data.get("param_name", "id"),
                payload=data.get("payload", "' OR 1=1 --"),
                method=data.get("method", "GET").upper(),
                notes=data.get("notes", "")
            )
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return self._get_default_context(finding)

    def _get_default_context(self, finding: UnifiedFinding) -> EnhancedContext:
        """Fallback context if LLM fails."""
        return EnhancedContext(
            target_url="http://localhost:8000",
            param_name="id",
            payload="' OR 1=1 --",
            method="GET"
        )

    def _build_prompt(self, finding: UnifiedFinding) -> str:
        return f"""
You are a Security Engineer generating a Proof-of-Concept (PoC).
Analyze the following vulnerability and extract parameters for the exploit.

Vulnerability: {finding.title}
File: {finding.file_path}
Code:
```
{finding.code_snippet}
```

Return a JSON object with:
- target_url: Probable URL endpoint (guess based on code/file path). Default to http://localhost:8000/...
- param_name: The name of the vulnerable parameter (e.g. "id", "username", "q").
- payload: A SAFE test payload to verify the vulnerability (e.g. "' OR 1=1 --" for SQLi, "<script>alert(1)</script>" for XSS).
- method: HTTP method (GET or POST).
- notes: Brief explanation.

Output JSON only.
"""

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Robust JSON parsing from LLM output."""
        try:
            # Strip code blocks if present
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from LLM response")
            return {}
