from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from flipkart.data_converter import DataConverter
from flipkart.config import Config
import os

class DataIngestor:
    def __init__(self, persist_directory="chroma_db"):
        self.persist_directory = persist_directory
        # Use HuggingFaceEmbeddings instead of HuggingFaceEndpointEmbeddings for local embeddings
        self.embedding = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def ingest(self, load_existing=True):
        if load_existing and os.path.exists(self.persist_directory):
            # Load existing Chroma vector store
            self.vstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding
            )
            return self.vstore

        # Create new vector store from documents
        docs = DataConverter("data/flipkart_product_review.csv").convert()

        self.vstore = Chroma.from_documents(
            documents=docs,
            embedding=self.embedding,
            persist_directory=self.persist_directory
        )

        return self.vstore

