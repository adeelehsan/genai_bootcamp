"""Graph builder for blog generation workflow."""

import logging
from langgraph.graph import StateGraph, START, END
from src.llms.openai_llm import OpenAILLM
from src.states.blogstate import BlogState
from src.nodes.blog_node import BlogNode

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build and configure LangGraph workflow for blog generation."""

    def __init__(self, llm):
        """
        Initialize GraphBuilder with LLM instance.

        Args:
            llm: LangChain LLM instance for content generation
        """
        self.llm = llm
        self.graph = StateGraph(BlogState)
        self.blog_node_obj = None

    def build_topic_graph(self):
        """
        Build a graph to generate blogs based on a topic.

        The graph flow:
        START -> title_creation -> content_generation -> END

        Returns:
            StateGraph: Configured state graph
        """
        logger.info("Building topic-based blog generation graph")

        self.blog_node_obj = BlogNode(self.llm)

        # Add nodes
        self.graph.add_node("title_creation", self.blog_node_obj.title_creation)
        self.graph.add_node("content_generation", self.blog_node_obj.content_generation)

        # Add edges
        self.graph.add_edge(START, "title_creation")
        self.graph.add_edge("title_creation", "content_generation")
        self.graph.add_edge("content_generation", END)

        return self.graph

    def setup_graph(self, usecase: str = "topic"):
        """
        Setup and compile the graph for a specific use case.

        Args:
            usecase: Type of graph to build (default: "topic")

        Returns:
            CompiledGraph: Compiled executable graph
        """
        if usecase == "topic":
            self.build_topic_graph()
        else:
            raise ValueError(f"Unknown usecase: {usecase}")

        return self.graph.compile()


# LangSmith LangGraph Studio configuration
# This creates a graph instance for visual debugging and deployment
try:
    llm = OpenAILLM(model="gpt-5-mini", temperature=0.7).get_llm()
    graph_builder = GraphBuilder(llm)
    graph = graph_builder.build_topic_graph().compile()
    logger.info("Graph successfully initialized for LangGraph Studio")
except Exception as e:
    logger.error(f"Failed to initialize graph for LangGraph Studio: {str(e)}")
    graph = None

