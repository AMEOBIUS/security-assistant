"""
NVIDIA LLM Client.

Implementation of BaseLLMClient for NVIDIA NIM API.
NVIDIA NIM uses an OpenAI-compatible interface.
"""

import logging
from typing import Optional

from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class NvidiaClient(OpenAIClient):
    """
    Client for NVIDIA NIM API.
    
    Inherits from OpenAIClient as NVIDIA uses compatible API.
    Default Base URL: https://integrate.api.nvidia.com/v1
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistralai/devstral-2-123b-instruct-2512",
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize NVIDIA client.
        
        Args:
            api_key: NVIDIA API Key (nvapi-...)
            model: Model name (default: Devstral 2 123B)
        """
        # NVIDIA NIM endpoint
        base_url = "https://integrate.api.nvidia.com/v1"
        
        super().__init__(
            api_key=api_key,
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            api_base=base_url,
            **kwargs
        )
        
    async def is_available(self) -> bool:
        """Check if NVIDIA API is available."""
        # NVIDIA requires specific model names for listing,
        # so we try a lightweight chat completion instead
        try:
            await self.chat(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
