"""
Base LLM Client Architecture.

Defines the abstract base class and common data structures for all LLM providers.
"""

import abc
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    
    content: str
    raw_response: Any = None
    model_used: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMConnectionError(LLMError):
    """Connection error (timeout, network issue)."""
    pass


class LLMAuthenticationError(LLMError):
    """Authentication error (invalid API key)."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class BaseLLMClient(abc.ABC):
    """
    Abstract base class for LLM clients.
    
    All providers (OpenAI, Anthropic, Ollama) must inherit from this class
    and implement the abstract methods.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key for the provider
            model: Default model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abc.abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion for a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse object
            
        Raises:
            LLMError: On API errors
        """
        pass

    @abc.abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat completion for a conversation history.
        
        Args:
            messages: List of message dicts (role, content)
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abc.abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the service is available and credentials are valid.
        
        Returns:
            True if available, False otherwise
        """
        pass

    async def stream_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion chunks (optional implementation).
        
        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError("Streaming not implemented for this provider")
        yield ""  # Keep generator type hint happy
