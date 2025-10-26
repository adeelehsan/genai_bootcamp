from typing import List
from enum import Enum


class EmbeddingType(Enum):
    OPENAI = "openai"
    CHROMA_DEFAULT = "chroma_default"


class EmbeddingModel:
    """
    Unified embedding interface supporting multiple embedding providers.

    Supports:
    - OpenAI embeddings (requires API key)
    - Chroma default embeddings (no API key needed)
    """

    def __init__(self, embedding_type: str = "chroma_default", api_key: str = None, model_name: str = None):
        """
        Initialize the embedding model.

        Args:
            embedding_type: Type of embedding ("openai", "chroma_default")
            api_key: API key for OpenAI embeddings (optional)
            model_name: Specific model name (optional, uses defaults if not provided)
        """
        self.embedding_type = embedding_type
        self.api_key = api_key
        self.model_name = model_name
        self._embedding_function = None

        self._initialize_embedding()

    def _initialize_embedding(self):
        """Initialize the appropriate embedding function based on type."""
        if self.embedding_type == EmbeddingType.OPENAI.value:
            from langchain_openai import OpenAIEmbeddings

            if not self.api_key:
                raise ValueError("OpenAI API key is required for OpenAI embeddings")

            model = self.model_name or "text-embedding-3-small"
            self._embedding_function = OpenAIEmbeddings(
                api_key=self.api_key,
                model=model
            )

        elif self.embedding_type == EmbeddingType.CHROMA_DEFAULT.value:
            from chromadb.utils import embedding_functions

            # Chroma's default embedding function (sentence-transformers based)
            self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
        else:
            raise ValueError(f"Unsupported embedding type: {self.embedding_type}")

    def get_embedding_function(self):
        """Return the underlying embedding function for use with vector stores."""
        return self._embedding_function

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if self.embedding_type == EmbeddingType.CHROMA_DEFAULT.value:
            # Chroma's default function has different interface
            return self._embedding_function(texts)
        else:
            # LangChain embeddings have embed_documents method
            return self._embedding_function.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        if self.embedding_type == EmbeddingType.CHROMA_DEFAULT.value:
            # Chroma's default function
            return self._embedding_function([text])[0]
        else:
            # LangChain embeddings have embed_query method
            return self._embedding_function.embed_query(text)

    @staticmethod
    def get_available_types() -> List[str]:
        """Return list of available embedding types."""
        return [e.value for e in EmbeddingType]

    @staticmethod
    def get_display_names() -> dict:
        """Return display names for embedding types."""
        return {
            EmbeddingType.OPENAI.value: "OpenAI Embeddings",
            EmbeddingType.CHROMA_DEFAULT.value: "Chroma Default"
        }
