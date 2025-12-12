"""Tests for LLM Clients."""

from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from security_assistant.llm import (
    AnthropicClient,
    LLMAuthenticationError,
    LLMResponse,
    NvidiaClient,
    OllamaClient,
    OpenAIClient,
)


@pytest.mark.asyncio
async def test_openai_client():
    """Test OpenAI client wrapper."""
    client = OpenAIClient(api_key="test")
    
    # Mock the internal client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Test response"
    mock_response.model = "gpt-4"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_response.usage.total_tokens = 15
    
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    response = await client.complete("Hello")
    
    assert isinstance(response, LLMResponse)
    assert response.content == "Test response"
    assert response.model_used == "gpt-4"
    assert response.token_usage["total_tokens"] == 15

@pytest.mark.asyncio
async def test_anthropic_client():
    """Test Anthropic client wrapper."""
    client = AnthropicClient(api_key="test")
    
    # Mock
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Claude response")]
    mock_response.model = "claude-3-opus"
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    
    client.client.messages.create = AsyncMock(return_value=mock_response)
    
    response = await client.complete("Hello")
    
    assert response.content == "Claude response"
    assert response.model_used == "claude-3-opus"

@pytest.mark.asyncio
async def test_ollama_client():
    """Test Ollama client wrapper."""
    client = OllamaClient(api_base="http://localhost:11434")
    
    # Mock httpx
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Llama response"},
            "model": "llama3",
            "prompt_eval_count": 10,
            "eval_count": 5,
            "done": True
        }
        mock_post.return_value = mock_response
        
        response = await client.complete("Hello")
        
        assert response.content == "Llama response"
        assert response.model_used == "llama3"

@pytest.mark.asyncio
async def test_nvidia_client():
    """Test NVIDIA client wrapper."""
    client = NvidiaClient(api_key="test")
    
    # NVIDIA client uses OpenAI SDK under the hood
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "NVIDIA response"
    mock_response.model = "mistralai/devstral-2-123b-instruct-2512"
    mock_response.usage.total_tokens = 20
    
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    response = await client.complete("Hello")
    
    assert response.content == "NVIDIA response"
    assert "devstral" in response.model_used
    assert str(client.client.base_url) == "https://integrate.api.nvidia.com/v1/"

@pytest.mark.asyncio
async def test_openai_auth_error():
    """Test OpenAI auth error handling."""
    client = OpenAIClient(api_key="invalid")
    
    client.client.chat.completions.create = AsyncMock(
        side_effect=openai.AuthenticationError(
            message="Invalid key",
            response=MagicMock(),
            body={}
        )
    )
    
    with pytest.raises(LLMAuthenticationError):
        await client.complete("Hello")
