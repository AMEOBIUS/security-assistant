"""
Anthropic LLM Client.

Implementation of BaseLLMClient for Anthropic API (Claude).
"""

import logging
from typing import Dict, List, Optional

import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import Message

from .base_client import (
    BaseLLMClient,
    LLMAuthenticationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponse,
)

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic API (Claude 3.5 Sonnet, Opus)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20240620",
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """Initialize Anthropic client."""
        super().__init__(api_key, model, timeout, max_retries, **kwargs)
        
        self.client = AsyncAnthropic(
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Messages API."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Chat completion."""
        try:
            # Prepare arguments
            request_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 4096,  # Anthropic requires max_tokens
                **kwargs
            }
            
            if system_prompt:
                request_kwargs["system"] = system_prompt

            response: Message = await self.client.messages.create(
                **request_kwargs
            )

            content = response.content[0].text
            
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }

            return LLMResponse(
                content=content,
                raw_response=response,
                model_used=response.model,
                token_usage=usage,
                finish_reason=response.stop_reason,
            )

        except anthropic.AuthenticationError as e:
            raise LLMAuthenticationError(f"Anthropic authentication failed: {e}") from e
        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}") from e
        except anthropic.APIConnectionError as e:
            raise LLMConnectionError(f"Anthropic connection error: {e}") from e
        except anthropic.APIError as e:
            raise LLMError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error in Anthropic client: {e}") from e

    async def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            # No dedicated list_models in Anthropic API yet, try a tiny cheap call
            await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False
