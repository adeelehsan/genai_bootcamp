"""
News Article Summarizer - Summarizes news articles using map-reduce strategy

This module handles:
- Fetching articles using newspaper3k
- Creating document chunks for processing
- Generating summaries using LLM
"""

from typing import Optional, Dict
from newspaper import Article
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base_summarizer import BaseSummarizer


class NewsArticleSummarizer(BaseSummarizer):
    """
    Dedicated news article summarizer with map-reduce strategy.

    Features:
    - Multi-provider support (OpenAI, Groq)
    - Detailed and concise summary modes
    - Built on LangChain's map-reduce chain
    - Clean separation from vector store/RAG
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.0,
    ):
        """
        Initialize the news summarizer.

        Args:
            provider: LLM provider ("openai" or "groq")
            model_name: Model name (e.g., "gpt-4o-mini", "llama-3.3-70b-versatile")
            api_key: API key for the provider
            temperature: Temperature for generation (default: 0.0 for deterministic)
        """
        super().__init__(provider, model_name, api_key, temperature)

        # Initialize text splitter for long articles
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=200, length_function=len
        )

    def fetch_content(self, url: str) -> Optional[Article]:
        """
        Fetch article content using newspaper3k

        Args:
            url: URL of the news article

        Returns:
            Article object or None if fetch fails
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article
        except Exception as e:
            print(f"Error fetching article: {e}")
            return None

    def create_documents(self, content: Article) -> list[Document]:
        """
        Create LangChain documents from article text

        Args:
            content: Article object

        Returns:
            List of Document objects
        """
        texts = self.text_splitter.split_text(content.text)
        docs = [Document(page_content=t) for t in texts]
        return docs

    def get_prompts(self, summary_type: str) -> tuple[str, str]:
        """
        Get map and combine prompt templates for news articles.

        Args:
            summary_type: 'detailed' or 'concise'

        Returns:
            Tuple of (map_prompt_template, combine_prompt_template)
        """
        if summary_type == "detailed":
            map_prompt_template = """Write a detailed summary of the following text:
            "{text}"
            DETAILED SUMMARY:"""

            combine_prompt_template = """Write a detailed summary of the following text that combines the previous summaries:
            "{text}"
            FINAL DETAILED SUMMARY:"""
        else:  # concise summary
            map_prompt_template = """Write a concise summary of the following text:
            "{text}"
            CONCISE SUMMARY:"""

            combine_prompt_template = """Write a concise summary of the following text that combines the previous summaries:
            "{text}"
            FINAL CONCISE SUMMARY:"""

        return map_prompt_template, combine_prompt_template

    def extract_metadata(self, content: Article, url: str) -> Dict:
        """
        Extract metadata from article.

        Args:
            content: Article object
            url: Source URL

        Returns:
            Dictionary with article metadata
        """
        return {
            "title": content.title,
            "authors": content.authors,
            "publish_date": str(content.publish_date) if content.publish_date else None,
        }
