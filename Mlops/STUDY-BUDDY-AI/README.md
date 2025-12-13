# Study Buddy AI - Multi-Model Edition

An AI-powered quiz generation application built with **LangChain Expression Language (LCEL)** supporting **multiple AI models** from different providers.

## ✨ Features

- **Multi-Model Support**: Choose from Groq (LLaMA, Mixtral) and OpenAI (GPT-4, GPT-3.5) models
- **LCEL Architecture**: Modern composable chains using LangChain Expression Language
- **Interactive UI**: Streamlit-based interface with real-time quiz generation
- **Flexible Question Types**: Multiple Choice and Fill in the Blank questions
- **Customizable**: Topic, difficulty level, and number of questions
- **Results Export**: Download quiz results as CSV

## 🤖 Supported AI Models

### Groq Models (Fast & Free)
- **LLaMA 3.1 8B Instant** - Fast inference, good for general questions
- **LLaMA 3.1 70B Versatile** - More powerful, better reasoning
- **Mixtral 8x7B** - Mixture of experts, balanced performance

### OpenAI Models (Premium)
- **GPT-4** - Most capable, best quality questions
- **GPT-4 Turbo** - Faster GPT-4 variant
- **GPT-3.5 Turbo** - Cost-effective, good quality

## What's New - LCEL Migration

This project has been refactored to use **LangChain Expression Language (LCEL)**, bringing modern composable chain patterns similar to sibling projects.

### Key Changes

#### 1. **New Folder Structure**
```
STUDY-BUDDY-AI/
├── app/
│   ├── common/              # Logger and custom exceptions
│   ├── components/          # Core application components
│   │   ├── llm.py          # LLM loader
│   │   ├── question_chain.py   # LCEL chains for question generation
│   │   ├── question_schemas.py  # Pydantic models
│   │   └── helpers.py      # QuizManager and utilities
│   ├── config/             # Configuration management
│   └── application.py      # Main Streamlit app
├── manifests/              # Kubernetes manifests
├── requirements.txt        # Updated with LCEL dependencies
├── Dockerfile              # Docker container configuration
└── setup.py                # Package installation
```

#### 2. **LCEL Chain Implementation**

**Before (Old Style):**
```python
response = self.llm.invoke(prompt.format(topic=topic, difficulty=difficulty))
parsed = parser.parse(response.content)
```

**After (LCEL Style):**
```python
# Build composable chain using pipe operator
mcq_chain = (
    {
        "topic": lambda x: x["topic"],
        "difficulty": lambda x: x["difficulty"],
        "format_instructions": lambda x: parser.get_format_instructions()
    }
    | prompt
    | llm
    | parser
)

# Invoke the chain
question = mcq_chain.invoke({"topic": topic, "difficulty": difficulty})
```

#### 3. **Updated Components**

- **`app/components/llm.py`**: Centralized LLM loading using ChatGroq
- **`app/components/question_chain.py`**: LCEL chains for MCQ and Fill Blank generation
- **`app/components/question_schemas.py`**: Pydantic models for structured outputs
- **`app/components/helpers.py`**: QuizManager with LCEL integration

#### 4. **Benefits of LCEL**

✅ **Composable**: Chain components using the `|` pipe operator
✅ **Readable**: Clear data flow from input → prompt → LLM → parser
✅ **Maintainable**: Easy to modify, extend, or replace components
✅ **Consistent**: Follows modern LangChain patterns used across projects
✅ **Streamable**: Built-in support for streaming responses (future enhancement)

## Architecture

### LCEL Chain Flow

```
Input Dict → Prompt Template → LLM → Parser → Structured Output
    ↓             ↓              ↓       ↓          ↓
{"topic": X}   MCQ_PROMPT    ChatGroq  Pydantic  MCQQuestion
```

### Components

1. **LLM Module** (`app/components/llm.py`)
   - Loads ChatGroq with configuration
   - Reusable across all chains

2. **Question Chain** (`app/components/question_chain.py`)
   - `create_mcq_chain()`: LCEL chain for Multiple Choice Questions
   - `create_fill_blank_chain()`: LCEL chain for Fill in the Blank Questions
   - Retry logic and validation

3. **Question Schemas** (`app/components/question_schemas.py`)
   - `MCQQuestion`: Pydantic model for MCQs
   - `FillBlankQuestion`: Pydantic model for Fill Blanks

4. **Quiz Manager** (`app/components/helpers.py`)
   - Orchestrates question generation using LCEL chains
   - Manages quiz lifecycle: generation → attempt → evaluation → results

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Configuration

Create a `.env` file with your API keys:

```env
# Required for Groq models
GROQ_API_KEY=your_groq_api_key_here

# Required for OpenAI models
OPENAI_API_KEY=your_openai_api_key_here
```

**Note:** You only need the API key for the provider you want to use. For example:
- If using only Groq models, you only need `GROQ_API_KEY`
- If using only OpenAI models, you only need `OPENAI_API_KEY`
- For both providers, add both keys

## Usage

### Run Locally
```bash
streamlit run app/application.py
```

### Run with Docker
```bash
# Build image
docker build -t study-buddy-ai .

# Run container
docker run -p 8501:8501 --env-file .env study-buddy-ai
```

## How to Use

1. **Select AI Model**: Choose from Groq or OpenAI models in the sidebar
2. **Configure Quiz**:
   - Select question type (Multiple Choice or Fill in the Blank)
   - Enter a topic (e.g., "Python Programming", "World History")
   - Choose difficulty level (Easy, Medium, Hard)
   - Set number of questions (1-10)
3. **Generate Quiz**: Click "Generate Quiz" button
4. **Take Quiz**: Answer the questions in the interface
5. **Submit & Review**: Submit to see results with correct answers
6. **Export**: Download results as CSV for later review

## LCEL vs Old Approach

| Aspect | Old Approach | LCEL Approach |
|--------|-------------|---------------|
| Chain Definition | Manual invoke + parse | Composable with `\|` |
| Prompt Format | `PromptTemplate` | `ChatPromptTemplate` |
| Data Flow | Imperative | Declarative |
| Extensibility | Modify code | Add components |
| Consistency | Project-specific | Standard pattern |

## Technical Stack

- **LangChain**: LCEL chains and components
- **LangChain Groq**: ChatGroq LLM integration
- **Streamlit**: Interactive web interface
- **Pydantic**: Data validation and parsing
- **Pandas**: Results management

## Dependencies

```
langchain              # Core LangChain library
langchain-groq         # Groq provider support
langchain-openai       # OpenAI provider support
langchain-core         # LCEL components
streamlit              # Web UI framework
pandas                 # Data management
python-dotenv          # Environment variables
pydantic              # Data validation
openai                # OpenAI API client
```

## API Keys

### Getting Groq API Key (Free)
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Add to `.env` as `GROQ_API_KEY`

### Getting OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key
5. Add to `.env` as `OPENAI_API_KEY`

## Future Enhancements

- [ ] Add more providers (Anthropic Claude, Cohere, etc.)
- [ ] Add streaming support for real-time question generation
- [ ] Implement RAG for context-aware questions from documents
- [ ] Add more question types (True/False, Matching, Short Answer)
- [ ] Multi-language support
- [ ] User authentication and quiz history
- [ ] Difficulty auto-adjustment based on performance

## License

This project follows the standard educational use license.

## Contributing

Contributions are welcome! Follow the LCEL patterns established in this codebase.
