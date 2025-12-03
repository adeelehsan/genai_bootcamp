from langchain_huggingface import HuggingFaceEmbeddings

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

def get_embedding_model():
    try:
        logger.info("Intializing our Huggingface embedding model")

        # Configure model with proper device settings for MPS/CPU compatibility
        model_kwargs = {'device': 'cpu'}  # Use CPU to avoid MPS meta tensor issues
        encode_kwargs = {'normalize_embeddings': True}

        model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        logger.info("Huggingface embedding model loaded sucesfully....")

        return model

    except Exception as e:
        error_message=CustomException("Error occured while loading embedding model" , e)
        logger.error(str(error_message))
        raise error_message