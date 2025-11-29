from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import CSVLoader

from langchain_huggingface import HuggingFaceEmbeddings

from dotenv import load_dotenv

load_dotenv()


class VectorStoreBuilder:
    def __init__(self, csv_path: str, persis_directory: str = "chroma_db"):
        self.csv_path = csv_path
        self.persis_directory = persis_directory
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def build_and_Save_vectorstore(self):
        loader = CSVLoader(self.csv_path, encoding="utf-8", metadata_columns=[])

        data = loader.load()

        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        text = splitter.split_documents(data)

        db = Chroma.from_documents(text, self.embeddings, persist_directory=self.persis_directory)
        db.persist()

    def load_vector_store(self):
        return Chroma(persist_directory=self.persis_directory, embedding_function=self.embeddings)
