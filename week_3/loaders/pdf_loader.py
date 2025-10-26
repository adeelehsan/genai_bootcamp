"""
PDF Loader - Load and process PDF documents

This module provides:
- PDF text extraction using PyPDFLoader
- Document chunking for RAG
- Metadata extraction
"""

import tempfile
import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base_loader import BaseLoader


class PDFLoader(BaseLoader):
    """
    Load and process PDF documents.

    Features:
    - Extract text from PDF files
    - Split into chunks for embedding
    - Preserve metadata (filename, page numbers)
    - Return structured documents
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize the PDFLoader.

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
        Not applicable for PDFs - use load_from_bytes instead.

        Args:
            url: Not used for PDF loader

        Returns:
            Empty list
        """
        raise NotImplementedError("PDFLoader does not support URL loading. Use load_from_bytes instead.")

    def load_from_bytes(self, pdf_bytes: bytes, filename: str) -> List[Document]:
        """
        Load content from PDF file bytes and return as LangChain documents.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Name of the PDF file

        Returns:
            List of Document objects containing the PDF content
        """
        temp_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file.flush()
                temp_path = temp_file.name

            # Load PDF
            loader = PyPDFLoader(temp_path)
            documents = loader.load()

            if not documents:
                raise ValueError("No content could be extracted from the PDF")

            # Create metadata
            metadata = {
                "source": filename,
                "title": filename,
                "type": "pdf",
                "num_pages": len(documents)
            }

            # Add metadata to all documents
            for i, doc in enumerate(documents):
                doc.metadata.update(metadata)
                doc.metadata["page"] = i + 1

            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)

            # Ensure all chunks have the same metadata
            for chunk in chunks:
                chunk.metadata.update(metadata)

            return chunks

        except Exception as e:
            raise Exception(f"Failed to load PDF: {str(e)}")

        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
