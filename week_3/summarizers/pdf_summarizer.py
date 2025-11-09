"""
PDF Document Summarizer - Summarizes PDF documents using map-reduce strategy

This module handles:
- Loading PDFs using PDFLoader
- Creating document chunks for processing
- Generating summaries using LLM
"""

from typing import Optional, Dict
from langchain_core.documents import Document
from .base_summarizer import BaseSummarizer
from loaders import PDFLoader


class PDFSummarizer(BaseSummarizer):
    """
    Dedicated PDF document summarizer with map-reduce strategy.

    Features:
    - Multi-provider support (OpenAI, Groq)
    - Detailed and concise summary modes
    - Built on LangChain's map-reduce chain
    - Uses PDFLoader for document processing
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        api_key: str,
        temperature: float = 0.0,
    ):
        """
        Initialize the PDF summarizer.

        Args:
            provider: LLM provider ("openai" or "groq")
            model_name: Model name (e.g., "gpt-4o-mini", "llama-3.3-70b-versatile")
            api_key: API key for the provider
            temperature: Temperature for generation (default: 0.0 for deterministic)
        """
        super().__init__(provider, model_name, api_key, temperature)

        # Initialize PDF loader
        self.pdf_loader = PDFLoader(
            chunk_size=2000,
            chunk_overlap=200
        )

    def fetch_content(self, file_data: tuple) -> Optional[tuple]:
        """
        Process PDF file bytes, returning documents and metadata.

        Args:
            file_data: Tuple of (pdf_bytes, filename)

        Returns:
            Tuple of (documents, file_info) or None if processing fails
        """
        try:
            pdf_bytes, filename = file_data

            # Load PDF
            documents = self.pdf_loader.load_from_bytes(pdf_bytes, filename)

            if not documents:
                raise ValueError("No content extracted from PDF")

            # Create file info
            file_info = {
                "filename": filename,
                "num_pages": documents[0].metadata.get("num_pages", 0) if documents else 0
            }

            return (documents, file_info)

        except Exception as e:
            print(f"Error processing PDF: {e}")
            return None

    def create_documents(self, content: tuple) -> list[Document]:
        """
        Extract documents from content tuple.

        Args:
            content: Tuple of (documents, file_info)

        Returns:
            List of Document objects
        """
        documents, file_info = content
        return documents

    def get_prompts(self, summary_type: str) -> tuple[str, str]:
        """
        Get map and combine prompt templates for PDF documents.

        Args:
            summary_type: 'detailed' or 'concise'

        Returns:
            Tuple of (map_prompt_template, combine_prompt_template)
        """
        if summary_type == "detailed":
            map_prompt_template = """Write a detailed summary of the following PDF document section:
            "{text}"
            DETAILED SUMMARY:"""

            combine_prompt_template = """Write a detailed summary of the following text that combines the previous summaries from a PDF document:
            "{text}"
            FINAL DETAILED SUMMARY:"""
        else:  # concise summary
            map_prompt_template = """Write a concise summary of the following PDF document section:
            "{text}"
            CONCISE SUMMARY:"""

            combine_prompt_template = """Write a concise summary of the following text that combines the previous summaries from a PDF document:
            "{text}"
            FINAL CONCISE SUMMARY:"""

        return map_prompt_template, combine_prompt_template

    def extract_metadata(self, content: tuple, url: str = None) -> Dict:
        """
        Extract metadata from file info.

        Args:
            content: Tuple of (documents, file_info)
            url: Not used for PDF (filename is used instead)

        Returns:
            Dictionary with PDF metadata
        """
        documents, file_info = content

        return {
            "filename": file_info['filename'],
            "num_pages": file_info['num_pages']
        }

    def summarize_from_bytes(self, pdf_bytes: bytes, filename: str, summary_type: str = "detailed") -> Dict:
        """
        Summarize a PDF from file bytes.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Name of the PDF file
            summary_type: 'detailed' or 'concise'

        Returns:
            Dictionary containing:
                - filename: Name of the PDF
                - num_pages: Number of pages
                - summary: Generated summary (dict with 'output_text')
                - model_info: Model type and name used
        """
        try:
            # Create file data tuple
            file_data = (pdf_bytes, filename)

            # Fetch content
            content = self.fetch_content(file_data)
            if not content:
                return {"error": "Failed to process PDF"}

            # Create documents
            docs = self.create_documents(content)

            # Create chain
            chain = self._create_summary_chain(summary_type)

            # Generate summary
            summary = chain.invoke(docs)

            # Extract metadata
            metadata = self.extract_metadata(content)

            # Add summary and model info
            metadata["summary"] = summary
            metadata["model_info"] = {
                "provider": self.provider,
                "name": self.model_name,
                "temperature": self.temperature
            }

            return metadata

        except Exception as e:
            return {"error": f"Failed to summarize PDF: {str(e)}"}
