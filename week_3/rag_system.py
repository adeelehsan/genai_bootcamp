from typing import List, Optional, Dict, Any
import chromadb
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from embeddings import EmbeddingModel
from llm_provider_factory import LLMProviderFactory
from loaders import NewsLoader, YouTubeLoader, PDFLoader
from appconfig import (
    NEWS_SYSTEM_MESSAGE,
    YOUTUBE_SYSTEM_MESSAGE,
    PDF_SYSTEM_MESSAGE,
    NEWS_PROMPT_TEMPLATE,
    YOUTUBE_PROMPT_TEMPLATE,
    PDF_PROMPT_TEMPLATE
)
import os
import shutil


class RAGSystem:
    """
    Retrieval-Augmented Generation system for content summarization.

    Features:
    - Index news articles and YouTube videos using ChromaDB
    - Semantic search and retrieval
    - Generate summaries using LLM with context
    - Support multiple embedding models
    - Chat interface with conversation history
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        collection_name: str = "news_articles",
        persist_directory: str = "./chroma_db"
    ):
        """
        Initialize the RAG system.

        Args:
            embedding_model: Embedding model instance
            provider: LLM provider ("openai" or "groq")
            model_name: Model name
            api_key: API key for the provider
            temperature: Temperature for generation
            collection_name: Name for the ChromaDB collection
            persist_directory: Directory to persist the vector store
        """
        self.embedding_model = embedding_model
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.vector_store = None
        self.news_loader = NewsLoader()
        self.youtube_loader = YouTubeLoader()
        self.pdf_loader = PDFLoader()

        # Create LLM using factory
        self.llm = LLMProviderFactory.create_llm(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature
        )

        # Initialize vector store
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store."""
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # For Chroma default embeddings, we need to use a different approach
        if self.embedding_model.embedding_type == "chroma_default":
            # Use chromadb directly for default embeddings
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_model.get_embedding_function()
                )
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_model.get_embedding_function()
                )
        else:
            # Use LangChain's Chroma wrapper for OpenAI and HuggingFace embeddings
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model.get_embedding_function(),
                persist_directory=self.persist_directory
            )

    def index_url(self, url: str) -> Dict[str, Any]:
        """
        Download, process, and index a news article from URL.

        Args:
            url: URL of the news article

        Returns:
            Dictionary with status and metadata
        """
        try:
            # Load and parse the URL
            documents = self.news_loader.load_url(url)

            if not documents:
                return {
                    "success": False,
                    "message": "No content extracted from URL",
                    "num_chunks": 0
                }

            # Index the documents
            self._add_documents(documents)

            return {
                "success": True,
                "message": f"Successfully indexed {len(documents)} chunks",
                "num_chunks": len(documents),
                "title": documents[0].metadata.get("title", "Unknown")
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error indexing URL: {str(e)}",
                "num_chunks": 0
            }

    def index_youtube_url(self, url: str) -> Dict[str, Any]:
        """
        Download, transcribe, and index a YouTube video.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with status and metadata
        """
        try:
            # Load and transcribe the YouTube video
            documents = self.youtube_loader.load_url(url)

            if not documents:
                return {
                    "success": False,
                    "message": "No content extracted from YouTube video",
                    "num_chunks": 0
                }

            # Index the documents
            self._add_documents(documents)

            return {
                "success": True,
                "message": f"Successfully indexed {len(documents)} chunks from video",
                "num_chunks": len(documents),
                "title": documents[0].metadata.get("title", "Unknown"),
                "duration": documents[0].metadata.get("duration", 0),
                "author": documents[0].metadata.get("author", "Unknown")
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error indexing YouTube video: {str(e)}",
                "num_chunks": 0
            }

    def index_pdf(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process and index a PDF document.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Name of the PDF file

        Returns:
            Dictionary with status and metadata
        """
        try:
            # Load and process the PDF
            documents = self.pdf_loader.load_from_bytes(pdf_bytes, filename)

            if not documents:
                return {
                    "success": False,
                    "message": "No content extracted from PDF",
                    "num_chunks": 0
                }

            # Index the documents
            self._add_documents(documents)

            # Get metadata from first document
            num_pages = documents[0].metadata.get("num_pages", 0) if documents else 0

            return {
                "success": True,
                "message": f"Successfully indexed {len(documents)} chunks from PDF",
                "num_chunks": len(documents),
                "title": filename,
                "num_pages": num_pages
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error indexing PDF: {str(e)}",
                "num_chunks": 0
            }

    def _add_documents(self, documents: List[Document]):
        """Add documents to the vector store."""
        if self.embedding_model.embedding_type == "chroma_default":
            # Use chromadb directly
            ids = [f"doc_{i}_{hash(doc.page_content)}" for i, doc in enumerate(documents)]
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
        else:
            # Use LangChain Chroma
            self.vector_store.add_documents(documents)

    def search(self, query: str, k: int = 4) -> List[Document]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        if self.embedding_model.embedding_type == "chroma_default":
            # Use chromadb directly
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )

            # Convert to Document objects
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, text in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    documents.append(Document(page_content=text, metadata=metadata))

            return documents
        else:
            # Use LangChain Chroma
            return self.vector_store.similarity_search(query, k=k)

    def chat(self, query: str, chat_history: List[Dict[str, str]] = None, content_type: str = "news") -> Dict[str, Any]:
        """
        Chat with the RAG system, maintaining conversation context.

        Args:
            query: User's current question
            chat_history: Previous conversation messages [{"role": "user/assistant", "content": "..."}]
            content_type: Type of content ("news", "youtube", or "pdf")

        Returns:
            Dictionary with response and metadata
        """
        try:
            if chat_history is None:
                chat_history = []

            # Retrieve relevant documents based on current query
            relevant_docs = self.search(query, k=4)

            if not relevant_docs:
                return {
                    "success": False,
                    "summary": "",
                    "error": "No relevant documents found"
                }

            # Build context from retrieved documents
            context_texts = []
            for i, doc in enumerate(relevant_docs, 1):
                context_texts.append(f"[Document {i}]\n{doc.page_content}\n")

            context = "\n".join(context_texts)

            # Build conversation history for LLM
            conversation_context = ""
            if chat_history:
                # Only include last 6 messages to avoid context overflow
                recent_history = chat_history[-6:]
                for msg in recent_history:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    conversation_context += f"{role}: {msg['content']}\n\n"

            # Create prompt based on content type
            if content_type == "youtube":
                system_content = YOUTUBE_SYSTEM_MESSAGE
                prompt = YOUTUBE_PROMPT_TEMPLATE.format(
                    conversation_context=conversation_context if conversation_context else "No previous conversation.",
                    context=context,
                    query=query
                )
            elif content_type == "pdf":
                system_content = PDF_SYSTEM_MESSAGE
                prompt = PDF_PROMPT_TEMPLATE.format(
                    conversation_context=conversation_context if conversation_context else "No previous conversation.",
                    context=context,
                    query=query
                )
            else:  # news
                system_content = NEWS_SYSTEM_MESSAGE
                prompt = NEWS_PROMPT_TEMPLATE.format(
                    conversation_context=conversation_context if conversation_context else "No previous conversation.",
                    context=context,
                    query=query
                )

            # Generate response
            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)

            # Extract unique references
            references = []
            seen_sources = set()
            for doc in relevant_docs:
                source_url = doc.metadata.get("source")
                title = doc.metadata.get("title", "Unknown Title")
                if source_url and source_url not in seen_sources:
                    seen_sources.add(source_url)
                    references.append({
                        "url": source_url,
                        "title": title,
                        "authors": doc.metadata.get("authors", "Unknown"),
                        "publish_date": doc.metadata.get("publish_date", "Unknown")
                    })

            return {
                "success": True,
                "summary": response.content,
                "num_chunks_retrieved": len(relevant_docs),
                "references": references
            }

        except Exception as e:
            return {
                "success": False,
                "summary": "",
                "error": f"Error in chat: {str(e)}"
            }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            if self.embedding_model.embedding_type == "chroma_default":
                count = self.collection.count()
            else:
                count = len(self.vector_store.get()['ids'])

            return {
                "success": True,
                "total_documents": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_all_indexed_articles(self) -> Dict[str, Any]:
        """
        Get all unique articles indexed in the vector store.

        Returns:
            Dictionary with list of articles and their metadata
        """
        try:
            if self.embedding_model.embedding_type == "chroma_default":
                # Get all documents
                all_data = self.collection.get()
                metadatas = all_data.get('metadatas', [])
            else:
                # Use LangChain Chroma
                all_data = self.vector_store.get()
                metadatas = all_data.get('metadatas', [])

            # Extract unique articles by URL
            articles = {}
            for metadata in metadatas:
                url = metadata.get('source')
                if url and url not in articles:
                    articles[url] = {
                        'url': url,
                        'title': metadata.get('title', 'Unknown'),
                        'authors': metadata.get('authors', 'Unknown'),
                        'publish_date': metadata.get('publish_date', 'Unknown')
                    }

            return {
                "success": True,
                "articles": list(articles.values()),
                "total_articles": len(articles)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "articles": []
            }

    def delete_article(self, url: str) -> Dict[str, Any]:
        """
        Delete all chunks of a specific article from the vector store.

        Args:
            url: URL of the article to delete

        Returns:
            Dictionary with status and message
        """
        try:
            if self.embedding_model.embedding_type == "chroma_default":
                # Get all documents
                all_data = self.collection.get()
                ids_to_delete = []

                # Find all IDs that belong to this URL
                for i, metadata in enumerate(all_data.get('metadatas', [])):
                    if metadata.get('source') == url:
                        ids_to_delete.append(all_data['ids'][i])

                if ids_to_delete:
                    self.collection.delete(ids=ids_to_delete)
                    return {
                        "success": True,
                        "message": f"Deleted {len(ids_to_delete)} chunks from article",
                        "chunks_deleted": len(ids_to_delete)
                    }
                else:
                    return {
                        "success": False,
                        "message": "Article not found in index"
                    }
            else:
                # Use LangChain Chroma
                all_data = self.vector_store.get()
                ids_to_delete = []

                for i, metadata in enumerate(all_data.get('metadatas', [])):
                    if metadata.get('source') == url:
                        ids_to_delete.append(all_data['ids'][i])

                if ids_to_delete:
                    self.vector_store.delete(ids=ids_to_delete)
                    return {
                        "success": True,
                        "message": f"Deleted {len(ids_to_delete)} chunks from article",
                        "chunks_deleted": len(ids_to_delete)
                    }
                else:
                    return {
                        "success": False,
                        "message": "Article not found in index"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error deleting article: {str(e)}"
            }

    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            if self.embedding_model.embedding_type == "chroma_default":
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_model.get_embedding_function()
                )
            else:
                # Delete and recreate the vector store
                if os.path.exists(self.persist_directory):
                    shutil.rmtree(self.persist_directory)
                self._initialize_vector_store()

            return {"success": True, "message": "Collection cleared successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
