import os
from dotenv import load_dotenv

load_dotenv(override=True)


class EnvConfig:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.elevenlabs_api_key = os.getenv("ELEVEN_LABS_API_KEY")  # Match .env variable name


env_config = EnvConfig()


# RAG System Prompts

# System Messages
NEWS_SYSTEM_MESSAGE = "You are a helpful AI assistant specialized in answering questions about news articles. Provide clear, accurate, and conversational responses."

YOUTUBE_SYSTEM_MESSAGE = "You are a helpful AI assistant specialized in answering questions about YouTube videos. Provide clear, accurate, and conversational responses based on video transcripts."

PDF_SYSTEM_MESSAGE = "You are a helpful AI assistant specialized in answering questions about PDF documents. Provide clear, accurate, and conversational responses based on document content."

# Prompt Templates
NEWS_PROMPT_TEMPLATE = """You are a helpful AI assistant answering questions about news articles.

Previous Conversation:
{conversation_context}

Retrieved Context from Articles:
{context}

Current Question: {query}

Instructions:
- Answer based on the retrieved context and conversation history
- If the question references previous conversation, use that context
- Be conversational and natural
- Cite specific details from the articles when relevant
- If the context doesn't contain enough information, say so

Answer:"""

YOUTUBE_PROMPT_TEMPLATE = """You are a helpful AI assistant answering questions about YouTube video content.

Previous Conversation:
{conversation_context}

Retrieved Context from Video Transcripts:
{context}

Current Question: {query}

Instructions:
- Answer based on the retrieved video transcript context and conversation history
- If the question references previous conversation, use that context
- Be conversational and natural
- Reference specific moments or topics from the video when relevant
- If the context doesn't contain enough information to answer, say so
- Remember you're discussing video content, so you can mention what was said, explained, or shown

Answer:"""

PDF_PROMPT_TEMPLATE = """You are a helpful AI assistant answering questions about PDF documents.

Previous Conversation:
{conversation_context}

Retrieved Context from Documents:
{context}

Current Question: {query}

Instructions:
- Answer based on the retrieved document context and conversation history
- If the question references previous conversation, use that context
- Be conversational and natural
- Reference specific sections or pages from the documents when relevant
- If the context doesn't contain enough information to answer, say so
- Provide accurate and detailed answers based on the document content

Answer:"""
