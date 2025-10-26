"""Configuration management for the blog generator application."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-5-mini")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

    # LangSmith Configuration (Optional)
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "blog-generator")

    # Application Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # Model Options - GPT-5 family only
    AVAILABLE_MODELS = [
        "gpt-5",
        "gpt-5-mini"
    ]

    # Supported Languages
    SUPPORTED_LANGUAGES = [
        "English", "Spanish", "French", "German", "Italian",
        "Portuguese", "Chinese", "Japanese", "Korean",
        "Arabic", "Hindi", "Russian", "Dutch", "Turkish", "Polish"
    ]

    DEFAULT_LANGUAGE = "English"

    @classmethod
    def validate(cls) -> bool:
        """
        Validate required configuration.

        Returns:
            bool: True if configuration is valid
        """
        if not cls.OPENAI_API_KEY:
            return False
        return True

    @classmethod
    def setup_langsmith(cls):
        """Set up LangSmith tracing if configured."""
        if cls.LANGCHAIN_API_KEY:
            os.environ["LANGSMITH_API_KEY"] = cls.LANGCHAIN_API_KEY

        if cls.LANGCHAIN_TRACING_V2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = cls.LANGCHAIN_PROJECT


# Initialize LangSmith on import
Config.setup_langsmith()
