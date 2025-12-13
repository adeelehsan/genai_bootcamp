import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model Configuration
TEMPERATURE = 0.9
MAX_RETRIES = 3

# Available Models Configuration
AVAILABLE_MODELS = {
    "Groq - LLaMA 3.1 8B": {
        "provider": "groq",
        "model_name": "llama-3.1-8b-instant",
        "api_key_env": "GROQ_API_KEY"
    },
    "Groq - LLaMA 3.1 70B": {
        "provider": "groq",
        "model_name": "llama-3.1-70b-versatile",
        "api_key_env": "GROQ_API_KEY"
    },
    "Groq - Mixtral 8x7B": {
        "provider": "groq",
        "model_name": "mixtral-8x7b-32768",
        "api_key_env": "GROQ_API_KEY"
    },
    "OpenAI - GPT-4": {
        "provider": "openai",
        "model_name": "gpt-4",
        "api_key_env": "OPENAI_API_KEY"
    },
    "OpenAI - GPT-4 Turbo": {
        "provider": "openai",
        "model_name": "gpt-4-turbo-preview",
        "api_key_env": "OPENAI_API_KEY"
    },
    "OpenAI - GPT-3.5 Turbo": {
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "api_key_env": "OPENAI_API_KEY"
    }
}
