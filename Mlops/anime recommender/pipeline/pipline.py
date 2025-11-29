import logging
from config.config import GROQ_API_KEY, MODEL_NAME
from src.recommender import AnimeRecommender
from src.vectorstore import VectorStoreBuilder
from utils.custom_exception import CustomException

logger = logging.getLogger(__name__)


class AnimeRecommendationPipeline:
    def __init__(self, persist_dir="chroma_db"):

        try:
            logger.info("Initializing Anime Recommendation Pipeline")
            vs_builder = VectorStoreBuilder(csv_path="", persis_directory=persist_dir)
            self.vectorstore = vs_builder.load_vector_store()
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )

            self.recommender = AnimeRecommender(self.retriever, GROQ_API_KEY, MODEL_NAME)
            logger.info("Pipeline initialized successfully...")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline {str(e)}")
            raise CustomException("Error during pipeline initialization", e)

    def get_recommendation(self, query):
        try:
            logger.info(f"Recived a query {query}")

            recommendation = self.recommender.ask(query)

            logger.info("Recommendation generated successfully ...")
            return recommendation
        except Exception as e:
            logger.error(f"Failed to get recommendation {str(e)}")
            raise CustomException("Error during getting recommendation", e)
