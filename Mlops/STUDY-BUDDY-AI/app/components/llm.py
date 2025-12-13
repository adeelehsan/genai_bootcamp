import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from app.config.config import GROQ_API_KEY, OPENAI_API_KEY, TEMPERATURE, AVAILABLE_MODELS
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

def load_llm(model_display_name: str = "Groq - LLaMA 3.1 8B", temperature: float = TEMPERATURE):
    """
    Load LLM based on model selection.
    Supports multiple providers: Groq, OpenAI

    Args:
        model_display_name: Display name of the model (e.g., "Groq - LLaMA 3.1 8B")
        temperature: Temperature setting for the model

    Returns:
        LLM instance or None if loading fails
    """
    try:
        if model_display_name not in AVAILABLE_MODELS:
            raise ValueError(f"Model {model_display_name} not found in available models")

        model_config = AVAILABLE_MODELS[model_display_name]
        provider = model_config["provider"]
        model_name = model_config["model_name"]

        logger.info(f"Loading LLM: {model_display_name} (Provider: {provider}, Model: {model_name})")

        if provider == "groq":
            if not GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not found in environment variables")

            llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name=model_name,
                temperature=temperature,
            )
            logger.info(f"Successfully loaded Groq model: {model_name}")

        elif provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in environment variables")

            llm = ChatOpenAI(
                openai_api_key=OPENAI_API_KEY,
                model_name=model_name,
                temperature=temperature,
            )
            logger.info(f"Successfully loaded OpenAI model: {model_name}")

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return llm

    except Exception as e:
        error_message = CustomException(f"Failed to load LLM: {model_display_name}", e)
        logger.error(str(error_message))
        return None
