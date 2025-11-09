"""
YouTube Video Summarizer - Summarizes YouTube videos using map-reduce strategy

This module handles:
- Downloading and transcribing videos using YouTubeLoader
- Creating document chunks for processing
- Generating summaries using LLM
"""

from typing import Optional, Dict
from langchain_core.documents import Document
from .base_summarizer import BaseSummarizer
from loaders import YouTubeLoader


class YouTubeVideoSummarizer(BaseSummarizer):
    """
    Dedicated YouTube video summarizer with map-reduce strategy.

    Features:
    - Multi-provider support (OpenAI, Groq)
    - Detailed and concise summary modes
    - Built on LangChain's map-reduce chain
    - Uses YouTubeLoader for download and transcription
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.0,
        whisper_model: str = "base"
    ):
        """
        Initialize the YouTube video summarizer.

        Args:
            provider: LLM provider ("openai" or "groq")
            model_name: Model name (e.g., "gpt-4o-mini", "llama-3.3-70b-versatile")
            api_key: API key for the provider
            temperature: Temperature for generation (default: 0.0 for deterministic)
            whisper_model: Whisper model size for transcription
        """
        super().__init__(provider, model_name, api_key, temperature)

        # Initialize YouTube loader
        self.youtube_loader = YouTubeLoader(
            whisper_model=whisper_model,
            chunk_size=2000,
            chunk_overlap=200
        )

    def fetch_content(self, url: str) -> Optional[tuple]:
        """
        Download and transcribe video, returning documents and metadata.

        Args:
            url: YouTube video URL

        Returns:
            Tuple of (documents, video_info) or None if fetch fails
        """
        try:
            # Get video info first
            video_info = self.youtube_loader.get_video_info(url)
            if not video_info:
                raise ValueError("Could not fetch video information")

            # Download and transcribe
            documents = self.youtube_loader.load_url(url)

            if not documents:
                raise ValueError("No transcript generated from video")

            return (documents, video_info)

        except Exception as e:
            print(f"Error fetching video: {e}")
            return None

    def create_documents(self, content: tuple) -> list[Document]:
        """
        Extract documents from content tuple.

        Args:
            content: Tuple of (documents, video_info)

        Returns:
            List of Document objects
        """
        documents, video_info = content
        return documents

    def get_prompts(self, summary_type: str) -> tuple[str, str]:
        """
        Get map and combine prompt templates for YouTube videos.

        Args:
            summary_type: 'detailed' or 'concise'

        Returns:
            Tuple of (map_prompt_template, combine_prompt_template)
        """
        if summary_type == "detailed":
            map_prompt_template = """Write a detailed summary of the following video transcript:
            "{text}"
            DETAILED SUMMARY:"""

            combine_prompt_template = """Write a detailed summary of the following text that combines the previous summaries from a YouTube video:
            "{text}"
            FINAL DETAILED SUMMARY:"""
        else:  # concise summary
            map_prompt_template = """Write a concise summary of the following video transcript:
            "{text}"
            CONCISE SUMMARY:"""

            combine_prompt_template = """Write a concise summary of the following text that combines the previous summaries from a YouTube video:
            "{text}"
            FINAL CONCISE SUMMARY:"""

        return map_prompt_template, combine_prompt_template

    def extract_metadata(self, content: tuple, url: str) -> Dict:
        """
        Extract metadata from video info.

        Args:
            content: Tuple of (documents, video_info)
            url: Source URL

        Returns:
            Dictionary with video metadata
        """
        documents, video_info = content

        # Format duration
        duration_str = f"{video_info['duration'] // 60} min {video_info['duration'] % 60} sec"

        return {
            "title": video_info['title'],
            "author": video_info['author'],
            "duration": video_info['duration'],
            "duration_str": duration_str,
            "upload_date": video_info['upload_date'],
        }
