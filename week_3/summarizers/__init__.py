"""
Summarizers Package

This package provides content summarization capabilities:
- BaseSummarizer: Abstract base class with shared functionality
- NewsArticleSummarizer: Summarizes news articles
- YouTubeVideoSummarizer: Summarizes YouTube videos
- PDFSummarizer: Summarizes PDF documents

All summarizers use the map-reduce strategy for handling long content.
"""

from .base_summarizer import BaseSummarizer
from .news_summarizer import NewsArticleSummarizer
from .youtube_summarizer import YouTubeVideoSummarizer
from .pdf_summarizer import PDFSummarizer

__all__ = ['BaseSummarizer', 'NewsArticleSummarizer', 'YouTubeVideoSummarizer', 'PDFSummarizer']
