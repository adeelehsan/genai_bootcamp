import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.components.llm import load_llm
from app.components.question_schemas import MCQQuestion, FillBlankQuestion
from app.config.config import MAX_RETRIES, PERSONAS
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

# MCQ Prompt Template with Persona
MCQ_PROMPT_TEMPLATE = """{persona_prompt}

Generate a {difficulty} multiple-choice question about {topic}.
Your question style should be: {question_style}

Return ONLY a JSON object with these exact fields:
- 'question': A clear, specific question that matches your persona's style
- 'options': An array of exactly 4 possible answers
- 'correct_answer': One of the options that is the correct answer

Example format:
{{
    "question": "What is the capital of France?",
    "options": ["London", "Berlin", "Paris", "Madrid"],
    "correct_answer": "Paris"
}}

{format_instructions}

Your response:"""

# Fill Blank Prompt Template with Persona
FILL_BLANK_PROMPT_TEMPLATE = """{persona_prompt}

Generate a {difficulty} fill-in-the-blank question about {topic}.
Your question style should be: {question_style}

Return ONLY a JSON object with these exact fields:
- 'question': A sentence with '___' marking where the blank should be (match your persona's style)
- 'answer': The correct word or phrase that belongs in the blank

Example format:
{{
    "question": "The capital of France is ___.",
    "answer": "Paris"
}}

{format_instructions}

Your response:"""


def create_mcq_chain(model_name: str = "Groq - LLaMA 3.1 8B", persona: str = "Friendly Tutor"):
    """Create LCEL chain for MCQ generation with persona."""
    try:
        logger.info(f"Creating MCQ chain using LCEL with model: {model_name}, persona: {persona}")

        llm = load_llm(model_display_name=model_name)
        if llm is None:
            raise CustomException("LLM not loaded")

        # Get persona configuration
        persona_config = PERSONAS.get(persona, PERSONAS["Friendly Tutor"])

        # Create parser for MCQ
        parser = PydanticOutputParser(pydantic_object=MCQQuestion)

        # Create prompt template
        prompt = ChatPromptTemplate.from_template(MCQ_PROMPT_TEMPLATE)

        # Build LCEL chain: prompt | llm | parser
        mcq_chain = (
            {
                "topic": lambda x: x["topic"],
                "difficulty": lambda x: x["difficulty"],
                "persona_prompt": lambda x: persona_config["system_prompt"],
                "question_style": lambda x: persona_config["question_style"],
                "format_instructions": lambda x: parser.get_format_instructions()
            }
            | prompt
            | llm
            | parser
        )

        logger.info("Successfully created MCQ chain using LCEL with persona")
        return mcq_chain

    except Exception as e:
        error_message = CustomException("Failed to create MCQ chain", e)
        logger.error(str(error_message))
        return None


def create_fill_blank_chain(model_name: str = "Groq - LLaMA 3.1 8B", persona: str = "Friendly Tutor"):
    """Create LCEL chain for Fill Blank generation with persona."""
    try:
        logger.info(f"Creating Fill Blank chain using LCEL with model: {model_name}, persona: {persona}")

        llm = load_llm(model_display_name=model_name)
        if llm is None:
            raise CustomException("LLM not loaded")

        # Get persona configuration
        persona_config = PERSONAS.get(persona, PERSONAS["Friendly Tutor"])

        # Create parser for Fill Blank
        parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)

        # Create prompt template
        prompt = ChatPromptTemplate.from_template(FILL_BLANK_PROMPT_TEMPLATE)

        # Build LCEL chain: prompt | llm | parser
        fill_blank_chain = (
            {
                "topic": lambda x: x["topic"],
                "difficulty": lambda x: x["difficulty"],
                "persona_prompt": lambda x: persona_config["system_prompt"],
                "question_style": lambda x: persona_config["question_style"],
                "format_instructions": lambda x: parser.get_format_instructions()
            }
            | prompt
            | llm
            | parser
        )

        logger.info("Successfully created Fill Blank chain using LCEL with persona")
        return fill_blank_chain

    except Exception as e:
        error_message = CustomException("Failed to create Fill Blank chain", e)
        logger.error(str(error_message))
        return None


def generate_mcq(topic: str, difficulty: str = 'medium', model_name: str = "Groq - LLaMA 3.1 8B", persona: str = "Friendly Tutor") -> MCQQuestion:
    """Generate MCQ using LCEL chain with retry logic and persona."""
    try:
        chain = create_mcq_chain(model_name=model_name, persona=persona)
        if chain is None:
            raise CustomException("MCQ chain could not be created")

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Generating MCQ for topic '{topic}' with difficulty '{difficulty}' and persona '{persona}' (attempt {attempt + 1}/{MAX_RETRIES})")

                # Invoke LCEL chain with input dict
                question = chain.invoke({"topic": topic, "difficulty": difficulty})

                # Validate MCQ structure
                if len(question.options) != 4 or question.correct_answer not in question.options:
                    raise ValueError("Invalid MCQ Structure")

                logger.info("Generated a valid MCQ Question")
                return question

            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    raise CustomException(f"MCQ generation failed after {MAX_RETRIES} attempts", e)

    except Exception as e:
        logger.error(f"Failed to generate MCQ: {str(e)}")
        raise CustomException("MCQ generation failed", e)


def generate_fill_blank(topic: str, difficulty: str = 'medium', model_name: str = "Groq - LLaMA 3.1 8B", persona: str = "Friendly Tutor") -> FillBlankQuestion:
    """Generate Fill Blank using LCEL chain with retry logic and persona."""
    try:
        chain = create_fill_blank_chain(model_name=model_name, persona=persona)
        if chain is None:
            raise CustomException("Fill Blank chain could not be created")

        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Generating Fill Blank for topic '{topic}' with difficulty '{difficulty}' and persona '{persona}' (attempt {attempt + 1}/{MAX_RETRIES})")

                # Invoke LCEL chain with input dict
                question = chain.invoke({"topic": topic, "difficulty": difficulty})

                # Validate Fill Blank structure
                if "___" not in question.question:
                    raise ValueError("Fill in blanks should contain '___'")

                logger.info("Generated a valid Fill in Blanks Question")
                return question

            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    raise CustomException(f"Fill Blank generation failed after {MAX_RETRIES} attempts", e)

    except Exception as e:
        logger.error(f"Failed to generate Fill Blank: {str(e)}")
        raise CustomException("Fill in blanks generation failed", e)
