"""
OpenAI LLM Client.

Implementation of BaseLLMClient for OpenAI API.
"""

import logging
from typing import Dict, List, Optional

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from .base_client import (
    BaseLLMClient,
    LLMAuthenticationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponse,
)

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API (GPT-4, GPT-3.5)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """Initialize OpenAI client."""
        super().__init__(api_key, model, timeout, max_retries, **kwargs)
        
        # Extract base_url/api_base from kwargs
        base_url = kwargs.get("base_url") or kwargs.get("api_base")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries,
            base_url=base_url,
        )

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Chat Completion API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
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
                **kwargs
            }
            
            if max_tokens:
                request_kwargs["max_tokens"] = max_tokens

            response: ChatCompletion = await self.client.chat.completions.create(
                **request_kwargs
            )

            content = response.choices[0].message.content or ""
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=content,
                raw_response=response,
                model_used=response.model,
                token_usage=usage,
                finish_reason=response.choices[0].finish_reason,
            )

        except openai.AuthenticationError as e:
            raise LLMAuthenticationError(f"OpenAI authentication failed: {e}") from e
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        except openai.APIConnectionError as e:
            raise LLMConnectionError(f"OpenAI connection error: {e}") from e
        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error in OpenAI client: {e}") from e

    async def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            # Simple cheap call to check connection
            await self.client.models.list()
            return True
        except Exception:
            return False
