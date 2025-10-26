# Content Summarizer with RAG

A multi-modal content summarization and RAG (Retrieval-Augmented Generation) application powered by LangChain, ChromaDB, and Streamlit. Supports news articles, YouTube videos, and PDF documents.

## Features

### 📰 News Articles
- **Quick Summarize**: Direct article summarization from URL
- **RAG Mode**: Index multiple articles and query across them
- Extract title, authors, publish date, and full content

### 🎥 YouTube Videos
- **Quick Summarize**: Video transcription and summarization
- **RAG Mode**: Index multiple videos and query across transcripts
- Automatic audio download and Whisper transcription
- Extract video metadata (title, channel, duration)

### 📄 PDF Documents
- **Quick Summarize**: Direct PDF document summarization
- **RAG Mode**: Index multiple PDFs and query across documents
- Extract text from multi-page PDFs
- Preserve document structure and metadata

### 🎙️ Voice Features
- **Speech-to-Text**: Record questions with your microphone (OpenAI Whisper)
- **Text-to-Speech**: Listen to summaries with AI voice (ElevenLabs)
- Audio playback for all responses

### 🤖 Multi-Provider LLM Support
- **Groq**: Fast inference with Llama models
- **OpenAI**: GPT models for high-quality summaries

### 🔍 Flexible Embeddings
- **OpenAI Embeddings**: High quality, requires API key
- **HuggingFace**: Open-source sentence transformers
- **Chroma Default**: Free, no configuration needed

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI                           │
│  (News | YouTube | PDF) × (Quick Summarize | RAG Mode)     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Content Loaders                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  News    │  │ YouTube  │  │   PDF    │                │
│  │  Loader  │  │  Loader  │  │  Loader  │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Summarizers                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  News    │  │ YouTube  │  │   PDF    │                │
│  │Summarizer│  │Summarizer│  │Summarizer│                │
│  └──────────┘  └──────────┘  └──────────┘                │
│         (Map-Reduce Strategy with LLM)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      RAG System                             │
│  ┌─────────────────────┐  ┌──────────────────┐            │
│  │   Vector Store      │  │   LLM Generator  │            │
│  │   (ChromaDB)        │  │  (Groq/OpenAI)   │            │
│  │  - Embeddings       │  │  - Chat          │            │
│  │  - Semantic Search  │  │  - Summarization │            │
│  └─────────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Speech Service                           │
│  ┌─────────────────────┐  ┌──────────────────┐            │
│  │  Speech-to-Text     │  │  Text-to-Speech  │            │
│  │  (OpenAI Whisper)   │  │  (ElevenLabs)    │            │
│  └─────────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Loaders** (`loaders/`)
   - `NewsLoader`: Downloads and parses news articles (newspaper3k)
   - `YouTubeLoader`: Downloads videos and transcribes audio (yt-dlp + Whisper)
   - `PDFLoader`: Extracts text from PDF files (PyPDF)
   - All loaders chunk content for RAG

2. **Summarizers** (`summarizers/`)
   - `NewsArticleSummarizer`: Summarizes news articles
   - `YouTubeVideoSummarizer`: Summarizes video transcripts
   - `PDFSummarizer`: Summarizes PDF documents
   - Map-reduce strategy for long content

3. **RAG System** (`rag_system.py`)
   - ChromaDB vector store for semantic search
   - Document indexing and retrieval
   - Chat interface with conversation history
   - Separate collections per content type

4. **LLM Provider** (`llm_provider_factory.py`)
   - Unified interface for Groq and OpenAI
   - Automatic model detection and configuration
   - Temperature and parameter control

5. **Embeddings** (`embeddings.py`)
   - OpenAI, HuggingFace, and Chroma embeddings
   - Compatible with ChromaDB
   - Easy provider switching

6. **Speech Service** (`speech_service.py`)
   - OpenAI Whisper for speech-to-text
   - ElevenLabs for text-to-speech
   - Audio recording and playback

## Installation

### 1. Clone and Navigate
```bash
cd week_3
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install ffmpeg (Required for YouTube)
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### 5. Configure API Keys
Create a `.env` file:
```bash
# Required for LLM (choose one or both)
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional for voice features
ELEVEN_LABS_API_KEY=your_elevenlabs_key_here
```

## Usage

### Start the Application
```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

### Quick Start Guide

#### 1. Configure Settings (Sidebar)
- Enter your API keys
- Select LLM provider (Groq or OpenAI)
- Choose model (e.g., llama-3.3-70b-versatile, gpt-4o)
- Select embedding model
- Adjust temperature (0.0-1.0)

#### 2. Choose Content Type
- **📰 News**: For news articles
- **🎥 YouTube**: For YouTube videos
- **📄 PDF Documents**: For PDF files

#### 3. Select Mode

**🚀 Quick Summarize**
- Enter URL or upload file
- Choose summary type (detailed/concise)
- Optional: Enable "Listen to summary" for audio
- Click summarize button

**🔍 RAG Mode**
- Index multiple sources
- View indexed content
- Chat with your indexed knowledge base
- Optional: Use voice input/output

### Example Workflows

#### News Article Summary
```
1. Select "📰 News" app
2. Select "🚀 Quick Summarize"
3. Enter: https://www.bbc.com/news/technology-...
4. Click "📝 Summarize Article"
5. Read or listen to summary
```

#### YouTube Video RAG
```
1. Select "🎥 YouTube" app
2. Select "🔍 RAG Mode"
3. Choose "📚 Index Videos"
4. Add multiple video URLs and index them
5. Switch to "💬 Chat Mode"
6. Ask: "What are the main topics discussed?"
7. Optional: Use microphone for voice questions
```

#### PDF Document Chat
```
1. Select "📄 PDF Documents" app
2. Select "🔍 RAG Mode"
3. Choose "📄 Index PDFs"
4. Upload multiple PDF files
5. Switch to "💬 Chat Mode"
6. Ask questions about the documents
7. Get answers with citations
```

## Project Structure

```
week_3/
├── streamlit_app.py           # Main Streamlit UI
├── loaders/
│   ├── __init__.py
│   ├── base_loader.py         # Abstract base loader
│   ├── news_loader.py         # News article loader
│   ├── youtube_loader.py      # YouTube video loader
│   └── pdf_loader.py          # PDF document loader
├── summarizers/
│   ├── __init__.py
│   ├── base_summarizer.py     # Abstract base summarizer
│   ├── news_summarizer.py     # News article summarizer
│   ├── youtube_summarizer.py  # YouTube video summarizer
│   └── pdf_summarizer.py      # PDF document summarizer
├── rag_system.py              # RAG implementation
├── embeddings.py              # Embedding models
├── llm_provider_factory.py    # LLM abstraction
├── speech_service.py          # Voice features
├── appconfig.py              # Configuration
├── requirements.txt          # Dependencies
├── .env.example             # Example environment
└── README.md               # This file
```

## Configuration Options

### LLM Providers

**Groq** (Fast, Cost-Effective)
- `llama-3.3-70b-versatile`: Best quality
- `llama-3.1-8b-instant`: Fastest
- `mixtral-8x7b-32768`: Large context

**OpenAI** (High Quality)
- `gpt-4o`: Most capable
- `gpt-4o-mini`: Balanced
- `gpt-3.5-turbo`: Fast and cheap

### Embedding Models

| Model | Cost | Quality | Speed | Local |
|-------|------|---------|-------|-------|
| OpenAI | Paid | High | Fast | No |
| HuggingFace | Free | Medium-High | Medium | Yes |
| Chroma Default | Free | Medium | Fast | Yes |

### Voice Settings

- **Speech-to-Text**: Requires OpenAI API key (Whisper)
- **Text-to-Speech**: Requires ElevenLabs API key
- Both features work independently

## Advanced Features

### Collection Management
- Each content type uses a separate ChromaDB collection
- Collections persist between sessions
- View and delete indexed items
- Clear entire collections

### Conversation History
- Chat mode maintains context
- Previous 6 messages included in prompts
- Clear chat to reset context

### Audio Features
- Record questions with microphone
- Play AI responses as audio
- Listen to summaries option in Quick Summarize
