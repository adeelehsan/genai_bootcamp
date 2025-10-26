"""LLM provider module for OpenAI integration."""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


class OpenAILLM:
    """OpenAI LLM provider with improved error handling and configuration."""

    def __init__(self, model: str = "gpt-5-mini", temperature: float = 0.7):
        """
        Initialize OpenAI LLM provider.

        Args:
            model: OpenAI model name (default: gpt-5-mini)
            temperature: Sampling temperature (default: 0.7)
        """
        load_dotenv()
        self.model = model
        self.temperature = temperature
        self.api_key: Optional[str] = None

    def get_llm(self) -> ChatOpenAI:
        """
        Get configured OpenAI LLM instance.

        Returns:
            ChatOpenAI: Configured LLM instance

        Raises:
            ValueError: If API key is not found or invalid
        """
        try:
            self.api_key = os.getenv("OPENAI_API_KEY")

            if not self.api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found in environment variables. "
                    "Please set it in your .env file or environment."
                )

            os.environ["OPENAI_API_KEY"] = self.api_key

            llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature
            )

            return llm

        except Exception as e:
            raise ValueError(f"Error occurred while initializing OpenAI LLM: {str(e)}")