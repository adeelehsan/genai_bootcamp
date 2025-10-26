"""
Reusable LLM Provider Factory

This module provides a centralized way to create LLM instances for any provider.
Designed to be reusable across different content types (News, YouTube, Voice, etc.)
"""

from typing import Optional, Dict, Any
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    GROQ = "groq"


class LLMProviderFactory:
    """
    Factory for creating LLM instances across different providers.

    This is a reusable abstraction that can be used by:
    - NewsArticleSummarizer
    - YouTubeSummarizer (future)
    - VoiceSummarizer (future)
    - Any other content summarizer
    """

    # Provider-specific model lists
    PROVIDER_MODELS = {
        LLMProvider.OPENAI: [
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
        ],
        LLMProvider.GROQ: [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]
    }

    @classmethod
    def create_llm(
        cls,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.0,
        **kwargs
    ) -> Any:
        """
        Create an LLM instance for the specified provider.

        Args:
            provider: Provider name ("openai" or "groq")
            model_name: Model name
            api_key: API key for the provider
            temperature: Temperature for generation (default: 0.0 for deterministic)
            **kwargs: Additional provider-specific arguments

        Returns:
            LLM instance (ChatOpenAI or ChatGroq)

        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        if not api_key:
            raise ValueError(f"API key is required for {provider}")

        provider_enum = LLMProvider(provider.lower())

        if provider_enum == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                temperature=temperature,
                **kwargs
            )

        elif provider_enum == LLMProvider.GROQ:
            return ChatGroq(
                model=model_name,
                groq_api_key=api_key,
                temperature=temperature,
                **kwargs
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @classmethod
    def get_models_for_provider(cls, provider: str) -> list[str]:
        """
        Get available models for a provider.

        Args:
            provider: Provider name ("openai" or "groq")

        Returns:
            List of available model names
        """
        provider_enum = LLMProvider(provider.lower())
        return cls.PROVIDER_MODELS.get(provider_enum, [])

    @classmethod
    def get_all_providers(cls) -> list[str]:
        """
        Get list of all supported providers.

        Returns:
            List of provider names
        """
        return [provider.value for provider in LLMProvider]

    @classmethod
    def detect_provider(cls, model_name: str) -> str:
        """
        Auto-detect provider from model name.

        Args:
            model_name: Model name

        Returns:
            Provider name ("openai" or "groq")
        """
        model_lower = model_name.lower()

        # Check OpenAI models
        for model in cls.PROVIDER_MODELS[LLMProvider.OPENAI]:
            if model.lower() in model_lower or model_lower.startswith("gpt"):
                return LLMProvider.OPENAI.value

        # Check Groq models
        for model in cls.PROVIDER_MODELS[LLMProvider.GROQ]:
            if model.lower() in model_lower or "llama" in model_lower or "mixtral" in model_lower:
                return LLMProvider.GROQ.value

        # Default to OpenAI
        return LLMProvider.OPENAI.value


class LLMConfig:
    """
    Configuration class for LLM settings.
    Makes it easy to pass around LLM configuration.
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.0,
        **kwargs
    ):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.kwargs = kwargs

    def create_llm(self) -> Any:
        """Create LLM instance from this configuration."""
        return LLMProviderFactory.create_llm(
            provider=self.provider,
            model_name=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            **self.kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "temperature": self.temperature,
            **self.kwargs
        }
