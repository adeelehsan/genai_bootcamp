"""
Configuration for Customer Support Chatbot
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# MCP Server
MCP_SERVER_URL = "https://vipfapwm3x.us-east-1.awsapprunner.com/mcp"

# GROQ API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast and capable

# Product Categories (from MCP server)
CATEGORIES = [
    "Computers",
    "Monitors",
    "Printers",
    "Accessories",
    "Networking"
]
