# AI Blog Generator

A professional AI-powered blog generation system built with **LangGraph**, **OpenAI**, **FastAPI**, and **Streamlit**. Generate high-quality, SEO-optimized blog posts automatically using a multi-stage LLM workflow.

## Features

- **AI-Powered Generation**: Uses OpenAI's GPT-5 models for intelligent content creation
- **Multilingual Support**: Generate blogs in 15 languages
- **Multi-Stage Workflow**: Separate title generation and content creation stages using LangGraph
- **REST API**: FastAPI backend for programmatic access
- **History Management**: Save and download previously generated blogs
- **Customizable**: Adjust model, temperature, language, and other parameters
- **Markdown Support**: Generated content in clean, formatted Markdown

## Multilingual Support

The blog generator supports **15 languages**! Generate professional content in:

- English, Spanish, French, German, Italian
- Portuguese, Chinese, Japanese, Korean
- Arabic, Hindi, Russian, Dutch, Turkish, Polish

## Architecture

The system uses **LangGraph** to orchestrate a state-based workflow:

```
Input Topic → Title Creation → Content Generation → Complete Blog
```

**Workflow Components:**
1. **Title Creation Node**: Generates titles
2. **Content Generation Node**: Creates detailed blog content
3. **State Management**: Maintains topic, language, title, and content through the workflow

## Project Structure

```
week_4/
├── src/
│   ├── graphs/
│   │   └── graph_builder.py      # LangGraph workflow definition
│   ├── llms/
│   │   └── openai_llm.py         # OpenAI LLM provider
│   ├── nodes/
│   │   └── blog_node.py          # Blog generation nodes
│   ├── states/
│   │   └── blogstate.py          # State models
│   └── config.py                 # Configuration management
├── app.py                         # FastAPI application
├── streamlit_app.py               # Streamlit UI
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Quick Start

### Prerequisites

- Python 3.13+
- OpenAI API key
- UV package manager (recommended) or pip

### Installation

**Option 1: Using UV (Recommended)**

```bash
cd week_4

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

**Option 2: Using pip**

```bash
cd week_4

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Required: OPENAI_API_KEY=your_openai_api_key_here
# Optional: LANGCHAIN_API_KEY=your_langsmith_api_key_here
```

## Usage

### Option 1: Streamlit UI (Recommended)

Launch the interactive web interface:

```bash
streamlit run streamlit_app.py
```

Open browser to `http://localhost:8501`

**Features:**
- Select from 15 languages with flag indicators
- Choose between GPT-5 or GPT-5-mini models
- Adjust temperature for creativity control
- Generate blogs with real-time progress
- View blog history with expandable cards
- Download as Markdown or plain text
- Statistics dashboard showing total blogs generated

**Black Sidebar Theme:**
- Sleek black background
- White text for excellent contrast
- Modern, professional appearance

### Option 2: FastAPI Backend

Start the REST API server:

```bash
python app.py
# Or: uvicorn app:app --reload
```

API available at `http://localhost:8000`

**Interactive API Documentation:**
Visit `http://localhost:8000/docs`

**Example API Request:**

```bash
curl -X POST "http://localhost:8000/blogs" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Artificial Intelligence in Healthcare",
    "language": "English",
    "model": "gpt-5-mini",
    "temperature": 0.7
  }'
```

**Example Response:**

```json
{
  "success": true,
  "topic": "Artificial Intelligence in Healthcare",
  "language": "English",
  "title": "Revolutionizing Healthcare: The AI Transformation",
  "content": "## Introduction\n\nArtificial Intelligence is transforming..."
}
```

**Generate in Different Language:**

```bash
curl -X POST "http://localhost:8000/blogs" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Inteligencia Artificial en la Medicina",
    "language": "Spanish",
    "model": "gpt-5-mini"
  }'
```

### Option 3: LangGraph Studio

For visual debugging and workflow inspection:

```bash
langgraph dev
```

Open browser to `http://127.0.0.1:8123`

### Testing API Locally

```bash
# Health check
curl http://localhost:8000/

# Generate blog
curl -X POST http://localhost:8000/blogs \
  -H "Content-Type: application/json" \
  -d '{"topic": "Climate Change Solutions", "language": "English"}'
```

## Technologies Used

- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [OpenAI GPT](https://openai.com/) - Language model
- [FastAPI](https://fastapi.tiangolo.com/) - REST API framework
- [Streamlit](https://streamlit.io/) - Web UI framework
- [Pydantic](https://pydantic.dev/) - Data validation
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

## How It Works

1. **Input**: User provides blog topic and language
2. **Title Generation**:
   - LLM generates SEO-friendly title in target language
   - Optimized for 50-60 characters
   - Includes relevant keywords
3. **Content Generation**:
   - LLM creates detailed blog content in target language
   - Structured with Markdown formatting
   - Includes introduction, body sections, and conclusion
4. **Output**: Complete blog post with title and content

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `LANGCHAIN_API_KEY` | LangSmith API key | Optional |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing | Optional |
| `LANGCHAIN_PROJECT` | LangSmith project name | Optional |

