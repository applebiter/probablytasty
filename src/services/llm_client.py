"""
LLM client abstraction layer.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum


class LLMProvider(Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    NONE = "none"


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Send a chat request to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response text from the LLM
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM client is properly configured and available."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._client = None
        
        if api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=api_key)
            except ImportError:
                print("Warning: OpenAI package not installed")
            except Exception as e:
                print(f"Warning: Failed to initialize OpenAI client: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Add system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return self._client is not None


class AnthropicClient(LLMClient):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self._client = None
        
        if api_key:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=api_key)
            except ImportError:
                print("Warning: Anthropic package not installed")
            except Exception as e:
                print(f"Warning: Failed to initialize Anthropic client: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        if not self._client:
            raise RuntimeError("Anthropic client not initialized")
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = self._client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            system=system_prompt or "",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.content[0].text
    
    def is_available(self) -> bool:
        return self._client is not None


class GoogleClient(LLMClient):
    """Google Gemini client."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self._client = None
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._client = genai.GenerativeModel(model)
            except ImportError:
                print("Warning: Google Generative AI package not installed")
            except Exception as e:
                print(f"Warning: Failed to initialize Google client: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        if not self._client:
            raise RuntimeError("Google client not initialized")
        
        # Combine system prompt and messages
        full_prompt = ""
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n"
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                full_prompt += f"User: {content}\n"
            elif role == "assistant":
                full_prompt += f"Assistant: {content}\n"
        
        response = self._client.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        
        return response.text
    
    def is_available(self) -> bool:
        return self._client is not None


class LLMRouter:
    """Router for selecting and using LLM providers."""
    
    def __init__(
        self,
        preferred_provider: LLMProvider = LLMProvider.OPENAI,
        openai_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        google_key: Optional[str] = None,
    ):
        self.preferred_provider = preferred_provider
        self.clients: Dict[LLMProvider, Optional[LLMClient]] = {
            LLMProvider.OPENAI: OpenAIClient(openai_key) if openai_key else None,
            LLMProvider.ANTHROPIC: AnthropicClient(anthropic_key) if anthropic_key else None,
            LLMProvider.GOOGLE: GoogleClient(google_key) if google_key else None,
            LLMProvider.NONE: None,
        }
    
    def get_available_client(self) -> Optional[LLMClient]:
        """Get an available LLM client, preferring the configured provider."""
        # Try preferred provider first
        if self.preferred_provider != LLMProvider.NONE:
            client = self.clients.get(self.preferred_provider)
            if client and client.is_available():
                return client
        
        # Fall back to any available provider
        for provider, client in self.clients.items():
            if provider != LLMProvider.NONE and client and client.is_available():
                return client
        
        return None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Optional[str]:
        """
        Send a chat request using an available LLM client.
        
        Returns:
            Response text, or None if no client is available
        """
        client = self.get_available_client()
        if not client:
            return None
        
        try:
            return client.chat(messages, system_prompt, temperature, max_tokens)
        except Exception as e:
            print(f"Error during LLM chat: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if any LLM client is available."""
        return self.get_available_client() is not None
