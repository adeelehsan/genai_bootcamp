"""Blog state models for LangGraph workflow."""

from typing import TypedDict, Optional
from pydantic import BaseModel, Field


class Blog(BaseModel):
    """Blog post model with title and content."""

    title: str = Field(description="The title of the blog post")
    content: str = Field(description="The main content of the blog post in Markdown format")
    language: str = Field(default="English", description="Language of the blog post")


class BlogState(TypedDict):
    """State object passed through the blog generation graph."""

    topic: str  # Input topic for blog generation
    language: str  # Target language for the blog (default: English)
    blog: Optional[Blog]  # Generated blog content
    error: Optional[str]  # Error message if generation fails
