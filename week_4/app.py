"""FastAPI application for blog generation service."""

import os
import logging
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.graphs.graph_builder import GraphBuilder
from src.llms.openai_llm import OpenAILLM

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Blog Generator API",
    description="Generate high-quality blog posts using AI",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure LangSmith (optional)
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
if langchain_api_key:
    os.environ["LANGSMITH_API_KEY"] = langchain_api_key
    logger.info("LangSmith tracking enabled")


class BlogRequest(BaseModel):
    """Request model for blog generation."""
    topic: str = Field(..., description="Topic for the blog post", min_length=3)
    language: str = Field(default="English", description="Target language for the blog post")
    model: str = Field(default="gpt-5-mini", description="OpenAI GPT-5 model to use (gpt-5 or gpt-5-mini)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")

    @classmethod
    def validate_model(cls, v):
        allowed_models = ["gpt-5", "gpt-5-mini"]
        if v not in allowed_models:
            raise ValueError(f"Model must be one of {allowed_models}. Got: {v}")
        return v


class BlogResponse(BaseModel):
    """Response model for generated blog."""
    success: bool
    topic: str
    language: str = None
    title: str = None
    content: str = None
    error: str = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Blog Generator",
        "version": "2.0.0"
    }


@app.post("/blogs", response_model=BlogResponse)
async def create_blog(blog_request: BlogRequest):
    """
    Generate a blog post based on the provided topic.

    Args:
        blog_request: Blog generation request with topic and parameters

    Returns:
        BlogResponse with generated blog or error message
    """
    try:
        logger.info(f"Received blog generation request for topic: {blog_request.topic}")

        # Initialize LLM
        openai_llm = OpenAILLM(
            model=blog_request.model,
            temperature=blog_request.temperature
        )
        llm = openai_llm.get_llm()

        # Build and execute graph
        graph_builder = GraphBuilder(llm)
        graph = graph_builder.setup_graph(usecase="topic")

        # Generate blog with language
        state = graph.invoke({
            "topic": blog_request.topic,
            "language": blog_request.language
        })

        # Check for errors in state
        if "error" in state and state["error"]:
            logger.error(f"Blog generation failed: {state['error']}")
            return BlogResponse(
                success=False,
                topic=blog_request.topic,
                language=blog_request.language,
                error=state["error"]
            )

        # Extract blog data
        blog = state.get("blog", {})

        logger.info(f"Successfully generated {blog_request.language} blog for topic: {blog_request.topic}")

        return BlogResponse(
            success=True,
            topic=blog_request.topic,
            language=blog.get("language", blog_request.language),
            title=blog.get("title", ""),
            content=blog.get("content", "")
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during blog generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/blogs/legacy")
async def create_blog_legacy(request: Request) -> Dict[str, Any]:
    """
    Legacy endpoint for backward compatibility.

    Deprecated: Use POST /blogs instead
    """
    try:
        data = await request.json()
        topic = data.get("topic", "")
        language = data.get("language", "English")

        if not topic:
            return JSONResponse(
                status_code=400,
                content={"error": "Topic is required"}
            )

        # Initialize LLM with defaults
        openai_llm = OpenAILLM()
        llm = openai_llm.get_llm()

        # Build and execute graph
        graph_builder = GraphBuilder(llm)
        graph = graph_builder.setup_graph(usecase="topic")
        state = graph.invoke({"topic": topic, "language": language})

        return {"data": state}

    except Exception as e:
        logger.error(f"Error in legacy endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

