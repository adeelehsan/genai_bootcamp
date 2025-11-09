# Week 3 Architecture Overview

## System Architecture

The Week 3 project implements a modular, extensible news summarization system with two distinct approaches:

1. **Direct Summarization** (NewsArticleSummarizer)
2. **RAG-based Querying** (RAGSystem)

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Interface                        │
│  ┌─────────────┐  ┌────────────────────────────────────┐   │
│  │  Chat Tab   │  │    News Summarizer Tab             │   │
│  └─────────────┘  │  ┌──────────┐  ┌─────────────────┐ │   │
│                   │  │  Quick   │  │   RAG Mode      │ │   │
│                   │  │Summarize │  │ (Index & Query) │ │   │
│                   │  └──────────┘  └─────────────────┘ │   │
│                   └────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                     │                   │
         │                     │                   │
         ▼                     ▼                   ▼
    ┌────────┐        ┌───────────────┐    ┌──────────┐
    │ LLMApp │        │NewsArticle    │    │RAGSystem │
    │(Legacy)│        │Summarizer     │    │          │
    └────────┘        └───────────────┘    └──────────┘
         │                     │                   │
         │                     │                   └──────┐
         ▼                     ▼                          │
    ┌─────────┐         ┌──────────┐           ┌──────────────┐
    │LLMModel │         │newspaper3k│           │EmbeddingModel│
    │         │         │+ LangChain│           │   ChromaDB   │
    └─────────┘         └──────────┘           └──────────────┘
         │                     │                          │
         ▼                     ▼                          ▼
  ┌───────────┐        ┌────────────┐           ┌─────────────┐
  │Groq/OpenAI│        │OpenAI/     │           │  Vector     │
  │   APIs    │        │ Ollama     │           │   Store     │
  └───────────┘        └────────────┘           └─────────────┘
```

## Module Breakdown

### 1. Core LLM Modules

#### `llm_models.py` - LLM Abstraction Layer
**Purpose:** Unified interface for multiple LLM providers

**Classes:**
- `LLMModel` - Main LLM wrapper
- `LLMProvider` - Enum for provider types

**Supports:**
- Groq (Llama 3.3, Llama 3.1)
- OpenAI (GPT-5, GPT-5-mini, GPT-5-nano)

**Key Methods:**
```python
generate(messages, temperature, max_tokens) -> str
chat(user_message, system_prompt, ...) -> str
supports_temperature() -> bool
```

#### `embeddings.py` - Embedding Model Manager
**Purpose:** Unified interface for embedding generation

**Classes:**
- `EmbeddingModel` - Main embedding wrapper
- `EmbeddingType` - Enum for embedding types

**Supports:**
- OpenAI Embeddings (text-embedding-3-small)
- Chroma Default (SentenceTransformers based)
- HuggingFace Sentence Transformers (all-MiniLM-L6-v2)

**Key Methods:**
```python
get_embedding_function() -> EmbeddingFunction
embed_documents(texts) -> List[List[float]]
embed_query(text) -> List[float]
```

### 2. Content Loaders

#### `news_loader.py` - News Article Loader
**Purpose:** Download and parse news articles using newspaper3k

**Classes:**
- `NewsLoader` - Article fetching and processing

**Features:**
- Downloads articles from URLs
- Extracts: title, text, authors, publish_date
- Splits into chunks (1000 chars, 200 overlap)
- Returns LangChain Documents

**Key Methods:**
```python
load_url(url) -> List[Document]
load_multiple_urls(urls) -> List[Document]
validate_url(url) -> bool
```

### 3. Summarization Systems

#### `news_summarizer.py` - Direct Summarization
**Purpose:** Quick, direct article summarization using map-reduce

**Classes:**
- `NewsArticleSummarizer` - Main summarizer class

**Features:**
- Supports OpenAI and Ollama models
- Two summary types: detailed, concise
- Uses LangChain's `load_summarize_chain`
- Stateless operation (no vector store)

**Workflow:**
```
URL → newspaper3k → Split → Map (summarize chunks) → Reduce → Final summary
```

**Key Methods:**
```python
fetch_article(url) -> Article
create_documents(text) -> List[Document]
summarize(url, summary_type) -> Dict
```

**Return Format:**
```python
{
    "title": str,
    "authors": List[str],
    "publish_date": str,
    "summary": {"output_text": str},
    "url": str,
    "model_info": {"type": str, "name": str}
}
```

#### `rag_system.py` - RAG-based System
**Purpose:** Multi-article knowledge base with semantic search

**Classes:**
- `RAGSystem` - Vector store + retrieval + generation

**Features:**
- ChromaDB persistent vector store
- Semantic search across indexed articles
- Map-reduce summarization on retrieved chunks
- Supports multiple embedding models

**Workflow:**
```
URL → newspaper3k → Split → Embed → Store in ChromaDB
Query → Embed → Retrieve top-k → Map-reduce → Summary
```

**Key Methods:**
```python
index_url(url) -> Dict
search(query, k) -> List[Document]
summarize_news(url, query) -> Dict
get_collection_stats() -> Dict
clear_collection() -> Dict
```

### 4. User Interface

#### `streamlit_app.py` - Main Application
**Purpose:** Web interface with multiple modes

**Structure:**
```
Sidebar:
  - API Keys (Groq, OpenAI)
  - LLM Model Selection
  - Embedding Model Selection
  - Parameters (temperature, max_tokens)
  - System Prompt
  - Clear Chat / Clear Index buttons

Tab 1 - Chat:
  - Traditional chat interface
  - Uses LLMApp (legacy wrapper)

Tab 2 - News Summarizer:
  Mode 1: Quick Summarize
    - Direct URL → Summary
    - Choose: OpenAI or Ollama
    - Choose: detailed or concise
    - No vector store

  Mode 2: RAG Mode
    - Index multiple articles
    - Build knowledge base
    - Query across articles
    - Persistent storage
```

### 5. Configuration

#### `appconfig.py` - Configuration Management
**Purpose:** Environment configuration and constants

**Features:**
- Loads `.env` file
- Provides `EnvConfig` class
- Default prompts and constants

#### `.env` - Environment Variables
```bash
GROQ_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Data Flow

### Quick Summarize Flow

```
User Input (URL)
    ↓
Validate API Key
    ↓
NewsArticleSummarizer.summarize()
    ↓
newspaper3k.Article.download()
    ↓
newspaper3k.Article.parse()
    ↓
RecursiveCharacterTextSplitter
    ↓
load_summarize_chain (map_reduce)
    ├─ Map: LLM.generate() × N chunks
    └─ Reduce: LLM.generate() × 1
    ↓
Return Dict with summary
    ↓
Display in Streamlit
```

### RAG Mode Flow

```
User Input (URL to index)
    ↓
RAGSystem.index_url()
    ↓
NewsLoader.load_url()
    ↓
newspaper3k parsing
    ↓
Split into chunks
    ↓
EmbeddingModel.embed_documents()
    ↓
ChromaDB.add(embeddings)
    ↓
Confirmation to user

---

User Query
    ↓
RAGSystem.summarize_news()
    ↓
EmbeddingModel.embed_query()
    ↓
ChromaDB.search(query_embedding, k=4)
    ↓
Retrieve top 4 chunks
    ↓
Map-reduce on chunks
    ├─ Map: Summarize each chunk
    └─ Reduce: Combine summaries
    ↓
Return final summary
    ↓
Display in Streamlit
```

## Design Patterns

### 1. Strategy Pattern
Different embedding and LLM strategies can be swapped:
```python
embedding_model = EmbeddingModel(embedding_type="openai")  # or "chroma_default"
llm_model = LLMModel(model_name="gpt-4o-mini")  # or "llama-3.3-70b-versatile"
```

### 2. Factory Pattern
Convenience functions for creating summarizers:
```python
summarize_with_openai(url, api_key, model)
summarize_with_ollama(url, model)
```

### 3. Template Method Pattern
Both summarizers follow the same high-level algorithm:
```
fetch_content() → process() → summarize() → return_result()
```

### 4. Adapter Pattern
`EmbeddingModel` adapts different embedding providers to a common interface

### 5. Separation of Concerns
- **Content Fetching**: `news_loader.py`
- **Summarization Logic**: `news_summarizer.py`, `rag_system.py`
- **UI Logic**: `streamlit_app.py`
- **Configuration**: `appconfig.py`

## Extensibility

The architecture is designed to be easily extended:

### Adding New Content Types

```python
# Future: youtube_summarizer.py
class YouTubeTranscriptSummarizer:
    def fetch_content(self, video_url):
        # Use youtube-transcript-api
        pass

    def create_documents(self, transcript):
        # Split transcript
        pass

    def summarize(self, video_url, summary_type):
        # Same interface as NewsArticleSummarizer
        pass
```

### Adding New Models

```python
# In llm_models.py
class LLMProvider(Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"  # New provider

# In LLMModel.__init__
elif self.provider == LLMProvider.ANTHROPIC:
    self.client = Anthropic(api_key=anthropic_api_key)
```

### Adding New Embedding Types

```python
# In embeddings.py
class EmbeddingType(Enum):
    OPENAI = "openai"
    CHROMA_DEFAULT = "chroma_default"
    SENTENCE_TRANSFORMER = "sentence_transformer"
    COHERE = "cohere"  # New embedding type
```

## Performance Considerations

### NewsArticleSummarizer
- **Speed**: Fast (single article)
- **Cost**: 5+ LLM calls (map-reduce)
- **Memory**: Low (stateless)
- **Scalability**: Good for one-off summaries

### RAGSystem
- **Speed**: Slower (indexing + retrieval)
- **Cost**: 5+ LLM calls + embedding costs
- **Memory**: High (persistent vector store)
- **Scalability**: Excellent for multiple articles

### Optimization Tips
1. **Caching**: Cache article summaries by URL hash
2. **Batching**: Process multiple articles in parallel
3. **Embedding Reuse**: Store embeddings with articles
4. **Smart Chunking**: Use semantic chunking vs fixed size
5. **Model Selection**: Use smaller models for map phase

## Security Considerations

1. **API Keys**: Stored in `.env`, not committed to git
2. **Input Validation**: URL validation before fetching
3. **Rate Limiting**: Respect API rate limits
4. **Error Handling**: Graceful failure, no sensitive data leaks
5. **Sandboxing**: newspaper3k safely parses HTML

## Testing Strategy

```
Unit Tests:
  - EmbeddingModel.embed_query()
  - LLMModel.generate()
  - NewsLoader.load_url()

Integration Tests:
  - NewsArticleSummarizer.summarize()
  - RAGSystem.index_url() + search()

End-to-End Tests:
  - Full Streamlit workflow
  - Multiple providers (OpenAI, Ollama)
  - Error conditions
```

## Future Roadmap

### Phase 1: Current (Week 3) ✅
- News article summarization
- OpenAI and Ollama support
- RAG with ChromaDB
- Streamlit interface

### Phase 2: Content Expansion
- YouTube video summarization
- Voice/audio transcription and summarization
- PDF document summarization
- Web page summarization (any URL)

### Phase 3: Enhanced RAG
- Multi-modal embeddings (text + images)
- Hierarchical summarization
- Citation tracking
- Source verification

### Phase 4: Advanced Features
- Batch processing
- Scheduled indexing
- API endpoints (FastAPI)
- Comparison mode (compare articles)
- Trend analysis (analyze multiple articles over time)

## Conclusion

The Week 3 architecture provides:

✅ **Modularity**: Each component is independent and replaceable
✅ **Extensibility**: Easy to add new content types and models
✅ **Flexibility**: Multiple modes for different use cases
✅ **Scalability**: RAG system can handle large knowledge bases
✅ **User-Friendly**: Clean Streamlit interface with clear options

The separation between `NewsArticleSummarizer` (quick, direct) and `RAGSystem` (comprehensive, searchable) gives users the best of both worlds.
