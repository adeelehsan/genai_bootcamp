"""
Loaders Package - Content loaders for various sources

This package provides loaders for different content types:
- BaseLoader: Abstract base class with shared functionality
- NewsLoader: Load and process news articles
- YouTubeLoader: Download and transcribe YouTube videos
- PDFLoader: Load and process PDF documents
"""

from .base_loader import BaseLoader
from .news_loader import NewsLoader
from .youtube_loader import YouTubeLoader
from .pdf_loader import PDFLoader

__all__ = ['BaseLoader', 'NewsLoader', 'YouTubeLoader', 'PDFLoader']
