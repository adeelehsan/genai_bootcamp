import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_MODEL = "llama-3.1-8b-instant"
    CHROMA_PERSIST_DIR = "chroma_db"