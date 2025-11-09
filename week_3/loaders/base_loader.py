"""
Base Loader - Shared functionality for all content loaders

This module provides common functionality that all loaders (News, YouTube, etc.) can inherit.
"""

from typing import List
from langchain_core.documents import Document
from abc import ABC, abstractmethod


class BaseLoader(ABC):
    """
    Abstract base class for content loaders.

    Provides common functionality like URL validation and batch loading.
    Subclasses must implement the load_url() method.
    """

    @abstractmethod
    def load_url(self, url: str) -> List[Document]:
        """
        Load content from a single URL.

        This method must be implemented by subclasses.

        Args:
            url: URL to load

        Returns:
            List of Document objects
        """
        pass

    def load_multiple_urls(self, urls: List[str]) -> List[Document]:
        """
        Load content from multiple URLs.

        Args:
            urls: List of URLs to load

        Returns:
            List of all documents from all URLs
        """
        all_documents = []
        errors = []

        for url in urls:
            try:
                documents = self.load_url(url)
                all_documents.extend(documents)
            except Exception as e:
                errors.append(f"Failed to load {url}: {str(e)}")

        if errors:
            print("Errors encountered:")
            for error in errors:
                print(f"  - {error}")

        return all_documents

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if a string is a valid URL.

        Args:
            url: URL string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
