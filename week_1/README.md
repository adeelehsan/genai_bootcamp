# GenAI Assistant: A Simple LLM Q&A Application

## 1. Overview

A minimal Q&A chat application with a Streamlit frontend. Supports Groq and OpenAI (GPT-5 family) models, automatic provider switching, a named chatbot persona, and robust .env loading for Streamlit.

## 2. Features

* **Groq and OpenAI API Integration:** Connects to both Groq API and OpenAI API to access a range of LLMs.
* **Configurable Models:** Users can select different LLMs (e.g., Llama 3.3 70B, Llama 3.1 8B, OpenAI GPT-5) from the dropdown.
* **Automatic Provider Switching:** Automatically detects the selected model and uses the appropriate API (Groq or OpenAI).
* **API Key Management:** Option to input API keys directly in the Streamlit frontend or load from environment variables.
* **API Key Validation:** Real-time warnings when a selected model requires a missing API key.
* **Adjustable Temperature:** Controls the randomness of model responses (0.0 - 2.0).
* **Max Tokens Control:** Sets the maximum length of generated responses (256 - 4096).
* **Named Chatbot Persona:** Chatbot operates under the name "GenAI Assistant" with a default system prompt.
* **Prompt Customization:** Define custom system prompts to guide the LLM's behavior and context.
* **Chat History:** Maintains conversation context across multiple messages.
* **Chat History Clearing:** A button to reset the current conversation.

## 3. Tools & Frameworks Used

* **Python:** The primary programming language (Python 3.11+ recommended).
* **Groq API:** For accessing open-source LLMs (Llama models).
* **OpenAI API:** For accessing GPT-5 family models.
* **Streamlit:** For building the interactive web frontend.
* **`python-dotenv`:** For loading environment variables (API keys).
* **`uv` (or `pip`, `conda`, `poetry`):** For virtual environment and dependency management.

## 4. Setup and Installation

### 4.1. Prerequisites

* Python 3.11 or higher installed
* A Groq API key (sign up at https://console.groq.com/ to get one)
* An OpenAI API key (optional, only needed for GPT-5 models, sign up at https://platform.openai.com/)

### 4.2. Clone the Repository

```bash
git clone https://github.com/adeelehsan/genai_bootcamp.git
cd genai_bootcamp/week_1
```

### 4.3. Virtual Environment Setup

#### Using `uv` (Recommended)

1. **Create a virtual environment:**
   ```bash
   uv venv .venv
   ```

2. **Activate the virtual environment:**
   * **On macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   * **On Windows (PowerShell):**
     ```bash
     .venv\Scripts\Activate.ps1
     ```
   * **On Windows (Command Prompt):**
     ```bash
     .venv\Scripts\activate.bat
     ```

3. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

#### Using `pip`

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate the virtual environment:**
   * **On macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   * **On Windows (PowerShell):**
     ```bash
     .venv\Scripts\Activate.ps1
     ```
   * **On Windows (Command Prompt):**
     ```bash
     .venv\Scripts\activate.bat
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 4.4. API Key Configuration

1. **Create a `.env` file** in the `week_1` directory.

2. **Add your API keys** to the `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   **Note:** You only need to add the API key for the provider you plan to use. For example:
   * If you only want to use Groq models, you only need `GROQ_API_KEY`
   * If you only want to use OpenAI GPT-5 models, you only need `OPENAI_API_KEY`

## 5. Usage

### 5.1. Running the Main LLM App in Command Line (for testing)

To test the core LLM functionality without the Streamlit frontend:

```bash
python main.py
```

The application will prompt you to enter questions in the console.

### 5.2. Running the Streamlit Web Application

To launch the interactive web interface:

```bash
streamlit run streamlit_app.py
```

This will open the application in your web browser (usually at http://localhost:8501). You can then:

* **Enter your API Keys** in the sidebar (optional if already set in `.env`).
* **Select a Model** from the dropdown menu:
  * `llama-3.3-70b-versatile` (Groq) - Default
  * `llama-3.1-8b-instant` (Groq)
  * `openai/gpt-oss-120b` (Groq)
  * `gpt-5` (OpenAI)
  * `gpt-5-mini` (OpenAI)
  * `gpt-5-nano` (OpenAI)
* **Adjust Temperature** (0.0 - 2.0, default: 0.7) - Controls response randomness
* **Adjust Max Tokens** (256 - 4096, default: 1024) - Controls response length
* **Customize the System Prompt** (optional) - Override the default GenAI Assistant persona
* **Type your questions** in the chat input and receive responses
* **Click "Clear Chat"** to reset the conversation history

## 6. Project Structure

```
week_1/
├── .env                  # Environment variables (GROQ_API_KEY, OPENAI_API_KEY)
├── main.py               # Core LLM application logic and LLMApp class
├── appconfig.py          # Configuration for environment variables and chatbot settings
├── streamlit_app.py      # Streamlit web application frontend
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## 7. How It Works

### 7.1. Provider Detection

The application automatically detects which API to use based on the selected model:
* **GPT-5 models** → Uses OpenAI API
* **All other models** → Uses Groq API

### 7.2. API Key Validation

The application validates API keys in real-time:
* When you select a model, it checks if the required API key is present
* If missing, a warning appears in the sidebar: "⚠️ [Provider] API key required for this model"
* You cannot send messages until the required API key is provided

### 7.3. System Prompt

The chatbot has a default persona named "GenAI Assistant". You can:
* Use the default prompt (leave the System Prompt field empty)
* Provide a custom prompt (will be prefixed with "You are GenAI Assistant.")

## 8. Troubleshooting

### Issue: "API key required" error
**Solution:** Make sure you have the correct API key in your `.env` file or entered in the sidebar for the model you're using.

### Issue: "Model has been decommissioned" error
**Solution:** Some models may be deprecated over time. Select a different model from the dropdown.

### Issue: Streamlit app not loading
**Solution:**
1. Make sure you're in the `week_1` directory
2. Verify your virtual environment is activated
3. Run `pip install -r requirements.txt` to ensure all dependencies are installed

