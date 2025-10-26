import os
from dotenv import load_dotenv

load_dotenv(override=True)

CHATBOT_NAME = "GenAI Assistant"
DEFAULT_SYSTEM_PROMPT = f"""You are {CHATBOT_NAME}, a helpful and knowledgeable AI assistant.
You are designed to assist users with a wide range of tasks including answering questions,
providing explanations, helping with problem-solving, and engaging in meaningful conversations.
Always be polite, informative, and strive to provide accurate and helpful responses."""


class EnvConfig:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")


env_config = EnvConfig()
