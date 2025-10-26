"""
Base Summarizer - Abstract base class for content summarizers

This module provides shared functionality for all summarizers:
- LLM initialization using factory pattern
- Map-reduce chain setup
- Common summarization logic
"""

from abc import ABC, abstractmethod
from typing import Dict
from langchain_core.documents import Document
from langchain_classic.chains.summarize import load_summarize_chain
from langchain_core.prompts import PromptTemplate
from llm_provider_factory import LLMProviderFactory


class BaseSummarizer(ABC):
    """
    Abstract base class for content summarizers.

    Features:
    - Multi-provider LLM support (OpenAI, Groq)
    - Map-reduce summarization strategy
    - Detailed and concise summary modes
    - Reusable architecture
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.0,
    ):
        """
        Initialize the summarizer with specified provider and model.

        Args:
            provider: LLM provider ("openai" or "groq")
            model_name: Model name (e.g., "gpt-4o-mini", "llama-3.3-70b-versatile")
            api_key: API key for the provider
            temperature: Temperature for generation (default: 0.0 for deterministic)
        """
        if not api_key:
            raise ValueError(f"API key is required for {provider}")

        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature

        # Create LLM using the factory
        self.llm = LLMProviderFactory.create_llm(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature
        )

    @abstractmethod
    def fetch_content(self, url: str):
        """
        Fetch content from URL. Must be implemented by subclasses.

        Args:
            url: Content URL

        Returns:
            Content-specific object (Article, video info, etc.)
        """
        pass

    @abstractmethod
    def create_documents(self, content) -> list[Document]:
        """
        Create LangChain documents from content. Must be implemented by subclasses.

        Args:
            content: Content object to convert

        Returns:
            List of Document objects
        """
        pass

    @abstractmethod
    def get_prompts(self, summary_type: str) -> tuple[str, str]:
        """
        Get map and combine prompt templates. Must be implemented by subclasses.

        Args:
            summary_type: 'detailed' or 'concise'

        Returns:
            Tuple of (map_prompt_template, combine_prompt_template)
        """
        pass

    @abstractmethod
    def extract_metadata(self, content, url: str) -> Dict:
        """
        Extract metadata from content. Must be implemented by subclasses.

        Args:
            content: Content object
            url: Source URL

        Returns:
            Dictionary with content-specific metadata
        """
        pass

    def _create_summary_chain(self, summary_type: str):
        """
        Create the map-reduce summarization chain.

        Args:
            summary_type: 'detailed' or 'concise'

        Returns:
            Configured summarization chain
        """
        # Get prompts from subclass
        map_prompt_template, combine_prompt_template = self.get_prompts(summary_type)

        # Create prompt objects
        map_prompt = PromptTemplate(
            template=map_prompt_template, input_variables=["text"]
        )

        combine_prompt = PromptTemplate(
            template=combine_prompt_template, input_variables=["text"]
        )

        # Create and return chain
        return load_summarize_chain(
            llm=self.llm,
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=combine_prompt,
            verbose=True,
        )

    def summarize(self, url: str, summary_type: str = "detailed") -> Dict:
        """
        Main summarization pipeline using map-reduce strategy.

        Args:
            url: Content URL
            summary_type: 'detailed' or 'concise'

        Returns:
            Dictionary containing:
                - content-specific metadata
                - summary: Generated summary (dict with 'output_text')
                - url: Source URL
                - model_info: Model type and name used
        """
        try:
            # Fetch content (implemented by subclass)
            content = self.fetch_content(url)
            if not content:
                return {"error": "Failed to fetch content"}

            # Create documents (implemented by subclass)
            docs = self.create_documents(content)

            # Create chain
            chain = self._create_summary_chain(summary_type)

            # Generate summary
            summary = chain.invoke(docs)

            # Extract metadata (implemented by subclass)
            metadata = self.extract_metadata(content, url)

            # Add summary and model info
            metadata["summary"] = summary
            metadata["url"] = url
            metadata["model_info"] = {
                "provider": self.provider,
                "name": self.model_name,
                "temperature": self.temperature
            }

            return metadata

        except Exception as e:
            return {"error": f"Failed to summarize content: {str(e)}"}
