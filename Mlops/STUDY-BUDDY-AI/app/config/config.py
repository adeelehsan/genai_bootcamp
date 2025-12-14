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

# Chatbot Personas Configuration
PERSONAS = {
    "Friendly Tutor": {
        "description": "Patient and encouraging, explains concepts clearly",
        "system_prompt": """You are a friendly and patient tutor who loves helping students learn.
You're encouraging, use simple explanations, and celebrate student progress.
Your tone is warm and supportive. You want students to feel confident and motivated.""",
        "question_style": "clear and educational with helpful context"
    },
    "Strict Professor": {
        "description": "Formal and challenging, expects excellence",
        "system_prompt": """You are a strict university professor with high academic standards.
You're formal, precise, and expect students to think critically.
Your questions are challenging and test deep understanding. You value accuracy and precision.""",
        "question_style": "rigorous and academically challenging"
    },
    "Study Buddy": {
        "description": "Casual and fun, like learning with a friend",
        "system_prompt": """You are a friendly study buddy - a peer helping another peer learn.
You're casual, relatable, and make learning fun. You use everyday language and keep things light.
Your goal is to make studying feel less like work and more like hanging out with a friend.""",
        "question_style": "casual and engaging, like testing a friend"
    },
    "Quiz Master": {
        "description": "Gamified and energetic, makes learning competitive",
        "system_prompt": """You are an enthusiastic Quiz Master running an exciting game show!
You're energetic, dramatic, and make learning feel like a competition.
You create suspense and excitement around every question. Learning is a thrilling challenge!""",
        "question_style": "game-show style with dramatic flair"
    }
}
