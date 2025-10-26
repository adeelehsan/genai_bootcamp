"""
YouTube Video Loader - Downloads and transcribes YouTube videos

This module handles:
- Downloading YouTube videos using yt-dlp
- Extracting audio
- Transcribing using OpenAI Whisper
- Converting to LangChain Document format for RAG
"""

import os
import yt_dlp
import whisper
from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base_loader import BaseLoader


class YouTubeLoader(BaseLoader):
    """
    Loads and processes YouTube videos for RAG indexing.

    Features:
    - Downloads video and extracts audio
    - Transcribes using Whisper
    - Splits into chunks for embedding
    - Returns LangChain Document objects
    """

    def __init__(
        self,
        whisper_model: str = "base",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        download_dir: str = "./downloads"
    ):
        """
        Initialize YouTube loader.

        Args:
            whisper_model: Whisper model size ("tiny", "base", "small", "medium", "large")
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
            download_dir: Directory for temporary downloads
        """
        self.whisper_model_name = whisper_model
        self.whisper_model = None  # Lazy load
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.download_dir = download_dir

        # Create download directory
        os.makedirs(download_dir, exist_ok=True)

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def _load_whisper_model(self):
        """Lazy load Whisper model to save memory."""
        if self.whisper_model is None:
            print(f"Loading Whisper model: {self.whisper_model_name}...")
            self.whisper_model = whisper.load_model(self.whisper_model_name)

    def download_video(self, url: str) -> tuple[str, Dict]:
        """
        Download YouTube video and extract audio.

        Args:
            url: YouTube video URL

        Returns:
            Tuple of (audio_path, video_info)
        """
        print("Downloading video...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.download_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = os.path.join(self.download_dir, f"{info['id']}.mp3")

            video_info = {
                'title': info.get('title', 'Unknown Title'),
                'author': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'upload_date': info.get('upload_date', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'description': info.get('description', '')[:500],  # First 500 chars
                'url': url
            }

            return audio_path, video_info

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text
        """
        print("Transcribing audio with Whisper...")
        self._load_whisper_model()

        result = self.whisper_model.transcribe(audio_path)
        return result['text']

    def load_url(self, url: str) -> List[Document]:
        """
        Download, transcribe, and process YouTube video into Document chunks.

        Args:
            url: YouTube video URL

        Returns:
            List of Document objects with metadata
        """
        audio_path = None

        try:
            # Download video
            audio_path, video_info = self.download_video(url)

            # Transcribe
            transcript = self.transcribe_audio(audio_path)

            # Split into chunks
            chunks = self.text_splitter.split_text(transcript)

            # Create Document objects
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        'source': url,
                        'title': video_info['title'],
                        'author': video_info['author'],
                        'duration': video_info['duration'],
                        'upload_date': video_info['upload_date'],
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'content_type': 'youtube_video'
                    }
                )
                documents.append(doc)

            print(f"Created {len(documents)} document chunks from video")
            return documents

        except Exception as e:
            print(f"Error loading YouTube video: {str(e)}")
            raise

        finally:
            # Clean up audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    print("Cleaned up audio file")
                except Exception as e:
                    print(f"Warning: Could not remove audio file: {str(e)}")

    def get_video_info(self, url: str) -> Dict:
        """
        Get video information without downloading.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary with video metadata
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return {
                'title': info.get('title', 'Unknown Title'),
                'author': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'upload_date': info.get('upload_date', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'url': url
            }
