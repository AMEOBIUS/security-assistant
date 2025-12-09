"""
Ollama LLM Client.

Implementation of BaseLLMClient for local Ollama API.
"""

import logging
from typing import Dict, List, Optional

import httpx

from .base_client import (
    BaseLLMClient,
    LLMConnectionError,
    LLMError,
    LLMResponse,
)

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Client for local Ollama API (Llama 3, Mistral, etc.)."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        model: str = "llama3",
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize Ollama client.
        
        Args:
            api_base: Base URL for Ollama (default: http://localhost:11434)
            model: Model to use
        """
        super().__init__(None, model, timeout, max_retries, **kwargs)
        self.api_base = (api_base or "http://localhost:11434").rstrip("/")
        self.api_url = f"{self.api_base}/api/chat"

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using chat endpoint."""
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
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.api_url, json=payload)
                
                if response.status_code != 200:
                    raise LLMError(f"Ollama API error: {response.status_code} - {response.text}")
                
                data = response.json()
                
                content = data.get("message", {}).get("content", "")
                
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                }

                return LLMResponse(
                    content=content,
                    raw_response=data,
                    model_used=data.get("model", self.model),
                    token_usage=usage,
                    finish_reason="stop" if data.get("done") else "unknown"
                )

        except httpx.ConnectError as e:
            raise LLMConnectionError(f"Ollama connection error (is Ollama running?): {e}") from e
        except httpx.TimeoutException as e:
            raise LLMConnectionError(f"Ollama request timed out: {e}") from e
        except Exception as e:
            raise LLMError(f"Unexpected error in Ollama client: {e}") from e

    async def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check version
                resp = await client.get(f"{self.api_base}/api/version")
                if resp.status_code != 200:
                    return False
                
                # Check tags (models)
                resp = await client.get(f"{self.api_base}/api/tags")
                if resp.status_code != 200:
                    return False
                
                models = [m["name"] for m in resp.json().get("models", [])]
                # Allow partial match (e.g. 'llama3:latest' matches 'llama3')
                return any(self.model in m for m in models)
                
        except Exception:
            return False
