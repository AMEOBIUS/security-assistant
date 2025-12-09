"""
LLM Integration Module for Security Assistant.

Provides multi-provider LLM support for:
- Explaining security findings in plain language
- Suggesting fixes with context-aware recommendations
- Analyzing code for potential vulnerabilities
- Natural language queries on scan results

Supported Providers:
- OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Ollama (Llama 3, Mistral, CodeLlama) - Local LLMs

Version: 1.0.0
"""

from .anthropic_client import AnthropicClient
from .base_client import (
    BaseLLMClient,
    LLMAuthenticationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponse,
)
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .nvidia_client import NvidiaClient

__all__ = [
    # Base
    "BaseLLMClient",
    "LLMResponse",
    "LLMError",
    "LLMConnectionError",
    "LLMRateLimitError",
    "LLMAuthenticationError",
    # Clients
    "OpenAIClient",
    "AnthropicClient",
    "OllamaClient",
    "NvidiaClient",
]
