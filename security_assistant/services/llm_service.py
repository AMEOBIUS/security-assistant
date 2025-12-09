"""
LLM Service Layer.

Orchestrates LLM operations, manages templates, and handles provider abstraction.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

from jinja2 import Template

from security_assistant.config import LLMProvider, SecurityAssistantConfig
from security_assistant.llm import (
    AnthropicClient,
    BaseLLMClient,
    LLMError,
    NvidiaClient,
    OllamaClient,
    OpenAIClient,
)

if TYPE_CHECKING:
    from security_assistant.orchestrator import UnifiedFinding

logger = logging.getLogger(__name__)


class LLMService:
    """
    High-level service for LLM operations.
    
    Handles:
    - Client initialization based on config
    - Prompt template management
    - Error handling and fallback
    """

    PROMPTS_DIR = Path(__file__).parent.parent / "llm" / "prompts"

    def __init__(self, config: SecurityAssistantConfig):
        """
        Initialize LLM service.
        
        Args:
            config: Main application configuration
        """
        self.config = config.llm
        self.client: Optional[BaseLLMClient] = None
        self._initialize_client()
        self._load_templates()

    def _initialize_client(self):
        """Initialize the appropriate LLM client based on configuration."""
        if self.config.provider == LLMProvider.DISABLED:
            logger.info("LLM integration is disabled")
            return

        try:
            if self.config.provider == LLMProvider.OPENAI:
                self.client = OpenAIClient(
                    api_key=self.config.api_key,
                    model=self.config.model or "gpt-4",
                    timeout=self.config.timeout,
                    max_retries=self.config.retries
                )
            elif self.config.provider == LLMProvider.ANTHROPIC:
                self.client = AnthropicClient(
                    api_key=self.config.api_key,
                    model=self.config.model or "claude-3-5-sonnet-20240620",
                    timeout=self.config.timeout,
                    max_retries=self.config.retries
                )
            elif self.config.provider == LLMProvider.OLLAMA:
                self.client = OllamaClient(
                    api_base=self.config.api_base,
                    model=self.config.model or "llama3",
                    timeout=self.config.timeout,
                    max_retries=self.config.retries
                )
            elif self.config.provider == LLMProvider.NVIDIA:
                self.client = NvidiaClient(
                    api_key=self.config.api_key,
                    model=self.config.model or "mistralai/devstral-2-123b-instruct-2512",
                    timeout=self.config.timeout,
                    max_retries=self.config.retries
                )
            
            logger.info(f"Initialized LLM client: {self.config.provider} ({self.config.model})")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.client = None

    def _load_templates(self):
        """Load Jinja2 templates from disk."""
        self.templates: Dict[str, Template] = {}
        try:
            for template_file in self.PROMPTS_DIR.glob("*.txt"):
                self.templates[template_file.stem] = Template(template_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {e}")

    async def is_available(self) -> bool:
        """Check if LLM service is ready."""
        if not self.client:
            return False
        return await self.client.is_available()

    async def explain_finding(self, finding: "UnifiedFinding") -> str:
        """
        Generate a plain-language explanation for a finding.
        
        Args:
            finding: The security finding to explain
            
        Returns:
            Explanation text
        """
        if not self.client:
            raise LLMError("LLM client not initialized")

        template = self.templates.get("explain_finding")
        if not template:
            raise LLMError("Template 'explain_finding' not found")

        prompt = template.render(finding=finding)
        
        try:
            response = await self.client.complete(prompt, temperature=0.5)
            return response.content
        except Exception as e:
            logger.error(f"Error explaining finding {finding.finding_id}: {e}")
            raise

    async def suggest_fix(self, finding: "UnifiedFinding") -> str:
        """
        Suggest a code fix for a finding.
        
        Args:
            finding: The security finding
            
        Returns:
            Suggested fix (code snippet)
        """
        if not self.client:
            raise LLMError("LLM client not initialized")

        template = self.templates.get("suggest_fix")
        if not template:
            raise LLMError("Template 'suggest_fix' not found")

        # Determine file type from extension
        file_type = Path(finding.file_path).suffix.lstrip(".")
        
        prompt = template.render(
            finding=finding,
            file_type=file_type
        )
        
        try:
            response = await self.client.complete(prompt, temperature=0.2)
            return response.content
        except Exception as e:
            logger.error(f"Error suggesting fix for {finding.finding_id}: {e}")
            raise

    async def analyze_code(self, code: str, file_path: str) -> str:
        """
        Analyze code snippet for vulnerabilities.
        
        Args:
            code: Source code content
            file_path: Path to the file (for context)
            
        Returns:
            JSON string with findings
        """
        if not self.client:
            raise LLMError("LLM client not initialized")

        template = self.templates.get("analyze_code")
        if not template:
            raise LLMError("Template 'analyze_code' not found")

        file_type = Path(file_path).suffix.lstrip(".")

        prompt = template.render(
            code_content=code,
            file_path=file_path,
            file_type=file_type
        )
        
        try:
            # Force JSON mode for OpenAI if possible, but keep it generic for now
            response = await self.client.complete(prompt, temperature=0.1)
            return response.content
        except Exception as e:
            logger.error(f"Error analyzing code in {file_path}: {e}")
            raise
