from typing import List, Optional
from newspaper import Article
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base_loader import BaseLoader


class NewsLoader(BaseLoader):
    """
    Load and process news articles from URLs using newspaper3k.

    Features:
    - Download and parse news articles
    - Extract title, text, authors, and publish date
    - Split into chunks for embedding
    - Return structured documents
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize the NewsLoader.

        Args:
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def load_url(self, url: str) -> List[Document]:
        """
        Load content from a URL and return as LangChain documents.

        Args:
            url: URL of the news article

        Returns:
            List of Document objects containing the article content
        """
        try:
            # Create Article object
            article = Article(url)

            # Download and parse the article
            article.download()
            article.parse()

            # Extract information
            title = article.title or "Unknown Title"
            text = article.text
            authors = article.authors
            publish_date = article.publish_date

            if not text or len(text.strip()) < 100:
                raise ValueError("Could not extract meaningful content from the URL")

            # Create metadata
            metadata = {
                "source": url,
                "title": title,
                "authors": ", ".join(authors) if authors else "Unknown",
                "publish_date": str(publish_date) if publish_date else "Unknown"
            }

            # Create a single document with full content
            full_document = Document(
                page_content=f"Title: {title}\n\n{text}",
                metadata=metadata
            )

            # Split into chunks
            documents = self.text_splitter.split_documents([full_document])

            # Ensure all chunks have the same metadata
            for doc in documents:
                doc.metadata.update(metadata)

            return documents

        except Exception as e:
            raise Exception(f"Failed to load article: {str(e)}")
