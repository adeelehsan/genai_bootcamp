from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from src.prompt_template import get_anime_prompt


class AnimeRecommender:
    def __init__(self, retriever, api_key: str, model_name: str):
        self.retriever = retriever
        self.llm = ChatGroq(api_key=api_key, model=model_name, temperature=0)

        # Get the prompt template
        self.prompt = get_anime_prompt()

        # Build the chain using LCEL
        self.chain = (
            RunnableParallel({
                "context": self.retriever,
                "question": RunnablePassthrough()
            })
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def ask(self, question: str) -> str:
        """Ask a question and get an answer"""
        return self.chain.invoke(question)
