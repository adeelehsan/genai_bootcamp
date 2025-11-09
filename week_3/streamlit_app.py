import streamlit as st
from appconfig import env_config
from embeddings import EmbeddingModel
from rag_system import RAGSystem
from summarizers import NewsArticleSummarizer, YouTubeVideoSummarizer, PDFSummarizer
from llm_provider_factory import LLMProviderFactory
from speech_service import SpeechService
from audio_recorder_streamlit import audio_recorder
import tempfile
import os
import subprocess

# Constants
MODE_CHAT = "💬 Chat Mode"
MODE_INDEX = "📚 Index Articles"
MODE_VIEW = "👁️ View Indexed Articles"

# Helper Functions


def convert_wav_to_mp3(audio_bytes):
    """Convert WAV audio bytes to MP3 using ffmpeg with volume boost."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as input_file:
            input_file.write(audio_bytes)
            input_file.flush()
            input_path = input_file.name

        output_path = input_path.replace(".wav", ".mp3")

        subprocess.run([
            "ffmpeg",
            "-i", input_path,
            "-af", "volume=2.0",
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            "-y",
            output_path
        ], capture_output=True, check=True)

        with open(output_path, "rb") as mp3_file:
            mp3_bytes = mp3_file.read()

        os.unlink(input_path)
        os.unlink(output_path)

        return mp3_bytes

    except Exception:
        return audio_bytes


def display_audio_player(audio_data, is_tts=False):
    """Display audio player for recorded or TTS audio."""
    try:
        if is_tts:
            st.audio(audio_data, format="audio/mp3")
        else:
            mp3_data = convert_wav_to_mp3(audio_data)
            if len(mp3_data) < 10000:
                st.warning("⚠️ Audio file is very small - microphone may not be working. Please check browser microphone permissions.")
            st.audio(mp3_data, format="audio/mp3")
    except Exception as e:
        st.caption(f"⚠️ Audio playback error: {str(e)}" if not is_tts else "⚠️ Audio playback unavailable")


def display_chat_messages(messages):
    """Display chat messages with references and audio playback."""
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "user" and message.get("audio_data"):
                st.caption("🎤 Your recording:")
                display_audio_player(message["audio_data"], is_tts=False)

            if message["role"] == "assistant" and message.get("is_speech_response") and message.get("audio_data"):
                st.caption("🔊 Audio response:")
                display_audio_player(message["audio_data"], is_tts=True)

            if message["role"] == "assistant" and message.get("references"):
                with st.expander("📚 View References"):
                    for i, ref in enumerate(message["references"], 1):
                        st.markdown(f"**{i}.** [{ref['title']}]({ref['url']})")


def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        "rag_system": None,
        "current_embedding": None,
        "current_model": None,
        "current_collection": None,
        "indexed_urls": [],
        "chat_history": [],
        "processing_message": False,
        "current_app_mode": None,
        "speech_service": None,
        "last_audio_bytes": None
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def process_chat_message(query, rag_system, content_type="news"):
    """Process a chat message and return the result."""
    return rag_system.chat(
        query=query,
        chat_history=st.session_state.chat_history[:-1],
        content_type=content_type
    )


def initialize_rag_system(provider, model, api_key, temperature, embedding_choice, collection_name):
    """Initialize RAG system with given parameters."""
    embedding_api_key = api_key if embedding_choice == "openai" and provider == "openai" else None
    if embedding_choice == "openai" and provider != "openai":
        embedding_api_key = env_config.openai_api_key

    embedding_model = EmbeddingModel(
        embedding_type=embedding_choice,
        api_key=embedding_api_key
    )

    return RAGSystem(
        embedding_model=embedding_model,
        provider=provider,
        model_name=model,
        api_key=api_key,
        temperature=temperature,
        collection_name=collection_name
    )


def render_chat_interface(content_type="news"):
    """Render the chat interface for RAG mode."""
    articles_result = st.session_state.rag_system.get_all_indexed_articles()

    if content_type == "news":
        content_label = "articles"
    elif content_type == "youtube":
        content_label = "videos"
    else:
        content_label = "documents"

    if not articles_result["success"] or not articles_result["articles"]:
        st.warning(f"⚠️ No {content_label} indexed yet. Please index some {content_label} first in 'Index {content_label.title()}' mode.")
        return

    # Check if we need to process the last message
    if st.session_state.processing_message and st.session_state.chat_history:
        last_message = st.session_state.chat_history[-1]
        if last_message["role"] == "user":
            display_chat_messages(st.session_state.chat_history)

            # Show assistant thinking
            with st.chat_message("assistant"):
                with st.status("Thinking...", expanded=False) as status:
                    result = process_chat_message(
                        last_message["content"], st.session_state.rag_system, content_type=content_type)
                    status.update(
                        label="Complete!", state="complete", expanded=False)

                # Prepare response message
                response_msg = {
                    "role": "assistant",
                    "content": result["summary"] if result["success"] else f"❌ {result['error']}",
                    "references": result.get("references", []) if result["success"] else []
                }

                # Generate TTS audio if this was a speech-based question
                if last_message.get("is_speech_question") and st.session_state.speech_service and result["success"]:
                    with st.status("Generating audio response...", expanded=False) as audio_status:
                        audio_data = st.session_state.speech_service.generate_speech(result["summary"])
                        if audio_data:
                            response_msg["audio_data"] = audio_data
                            response_msg["is_speech_response"] = True
                        audio_status.update(label="Audio ready!", state="complete", expanded=False)

                st.session_state.chat_history.append(response_msg)

            st.session_state.processing_message = False
            st.rerun()
    else:
        display_chat_messages(st.session_state.chat_history)

        # Show clear chat button
        if st.session_state.chat_history:
            st.divider()
            col1, col2, col3 = st.columns([3, 1, 3])
            with col2:
                st.markdown('<div class="clear-chat-container">', unsafe_allow_html=True)
                if st.button(
                    "🗑️ Clear Chat",
                    type="tertiary",
                    key=f"clear_chat_{content_type}_btn"
                ):
                    st.session_state.chat_history = []
                    st.session_state.processing_message = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        if st.session_state.speech_service:
            st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
            col1, col2 = st.columns([20, 1])
            with col1:
                prompt_text = f"Ask a question about your indexed {content_label}..."
                text_prompt = st.chat_input(prompt_text, key=f"text_input_{content_type}")

            with col2:
                audio_bytes = audio_recorder(
                    pause_threshold=300.0,
                    sample_rate=16000,
                    text="",
                    icon_size="2x",
                    key=f"audio_recorder_{content_type}",
                    neutral_color="#1976D2",
                    recording_color="#e74c3c",
                    energy_threshold=(-1.0, 1.0)
                )
            st.markdown('</div>', unsafe_allow_html=True)

            if text_prompt:
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": text_prompt,
                    "is_speech_question": False
                })
                st.session_state.processing_message = True
                st.rerun()

            if audio_bytes and audio_bytes != st.session_state.last_audio_bytes:
                audio_size = len(audio_bytes)

                if audio_size > 5000:
                    st.session_state.last_audio_bytes = audio_bytes

                    with st.spinner("🎤 Transcribing your question..."):
                        try:
                            transcript = st.session_state.speech_service.transcribe_audio(audio_bytes, file_format="wav")

                            if not transcript or not transcript.strip():
                                st.error("❌ Unable to extract text from audio. Please try again and speak clearly.")
                                return

                            if len(transcript.strip()) < 3:
                                st.error("❌ Transcription too short. Please speak more clearly or for longer.")
                                return

                            st.session_state.chat_history.append({
                                "role": "user",
                                "content": transcript,
                                "is_speech_question": True,
                                "audio_data": audio_bytes
                            })
                            st.session_state.processing_message = True
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Transcription error: {str(e)}")
                else:
                    st.session_state.last_audio_bytes = audio_bytes
        else:
            prompt_text = f"Ask a question about your indexed {content_label}..."
            if prompt := st.chat_input(prompt_text):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": prompt,
                    "is_speech_question": False
                })
                st.session_state.processing_message = True
                st.rerun()


def render_view_indexed(content_type="news"):
    """Render the view indexed items interface."""
    if content_type == "news":
        content_label = "articles"
    elif content_type == "youtube":
        content_label = "videos"
    else:
        content_label = "documents"

    st.markdown(f"**View and manage indexed {content_label}**")

    articles_result = st.session_state.rag_system.get_all_indexed_articles()

    if articles_result["success"] and articles_result["articles"]:
        st.info(f"📊 {articles_result['total_articles']} {content_label} indexed")

        for i, article in enumerate(articles_result["articles"], 1):
            # For PDFs, use filename from URL if title is empty or 'Unknown'
            display_title = article['title']
            if content_type == "pdf" and (not display_title or display_title == "Unknown"):
                display_title = article['url']

            with st.expander(f"{i}. {display_title}", expanded=False):
                if content_type == "pdf":
                    st.markdown(f"**File:** {article['url']}")
                else:
                    st.markdown(f"**URL:** [{article['url']}]({article['url']})")

                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("🗑️ Delete", key=f"delete_{content_type}_{i}"):
                        with st.spinner(f"Deleting {content_label[:-1]}..."):
                            delete_result = st.session_state.rag_system.delete_article(article['url'])

                            if delete_result["success"]:
                                st.success(delete_result["message"])
                                if article['url'] in st.session_state.indexed_urls:
                                    st.session_state.indexed_urls.remove(article['url'])
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {delete_result.get('message', 'Unknown error')}")
    else:
        st.warning(f"No {content_label} indexed yet. Switch to 'Index {content_label.title()}' mode to add some.")


st.set_page_config(
    page_title="News Summarizer",
    page_icon="📰",
    layout="wide"
)

st.markdown("""
    <style>
    /* Secondary buttons - Blue by default */
    div.stButton > button[kind="secondary"],
    button[kind="secondary"],
    .stFormSubmitButton > button[kind="secondary"],
    div.stFormSubmitButton > button,
    button[type="submit"][kind="secondary"] {
        background-color: #1976D2 !important;
        color: white !important;
        border: 1px solid #1565C0 !important;
    }
    div.stButton > button[kind="secondary"]:hover,
    button[kind="secondary"]:hover,
    .stFormSubmitButton > button[kind="secondary"]:hover,
    div.stFormSubmitButton > button:hover,
    button[type="submit"][kind="secondary"]:hover {
        background-color: #1565C0 !important;
        border: 1px solid #0D47A1 !important;
    }

    /* Tertiary buttons - Dark/Background color */
    div.stButton > button[kind="tertiary"],
    button[kind="tertiary"],
    .clear-chat-container button,
    .clear-chat-container button[kind="tertiary"],
    .clear-chat-container div.stButton > button {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #4a4a4a !important;
    }
    div.stButton > button[kind="tertiary"]:hover,
    button[kind="tertiary"]:hover,
    .clear-chat-container button:hover,
    .clear-chat-container button[kind="tertiary"]:hover,
    .clear-chat-container div.stButton > button:hover {
        background-color: #3a3a3a !important;
        border: 1px solid #5a5a5a !important;
    }

    /* Clear Chat button container - Center the button */
    .clear-chat-container {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* Make Clear Chat button smaller and fit content */
    .clear-chat-container button,
    .clear-chat-container button[kind="tertiary"],
    .clear-chat-container div.stButton > button {
        font-size: 0.875rem !important;
        padding: 0.5rem 1.5rem !important;
        min-height: 2.25rem !important;
        height: auto !important;
        width: auto !important;
        min-width: 200px !important;
    }

    input[type="text"]:focus,
    input[type="text"]:focus-visible,
    input[type="text"]:active,
    input[type="password"]:focus,
    input[type="password"]:focus-visible,
    input[type="password"]:active,
    .stTextInput input:focus,
    .stTextInput input:focus-visible,
    .stTextInput input:active,
    .stTextInput > div > div > input:focus,
    .stTextInput > div > div > input:focus-visible,
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="input"] input:focus-visible {
        border-color: #1976D2 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    .stTextInput:focus-within,
    div[data-baseweb="input"]:focus-within {
        border-color: #1976D2 !important;
    }

    textarea,
    .stTextArea textarea,
    div[data-baseweb="textarea"] textarea {
        border-color: #90CAF9 !important;
    }
    textarea:focus,
    textarea:focus-visible,
    textarea:active,
    .stTextArea textarea:focus,
    .stTextArea textarea:focus-visible,
    .stTextArea textarea:active,
    div[data-baseweb="textarea"] textarea:focus,
    div[data-baseweb="textarea"] textarea:focus-visible,
    div[data-baseweb="textarea"] textarea:active {
        border-color: #1976D2 !important;
        box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.25) !important;
        outline: none !important;
    }

    .stTextArea:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #1976D2 !important;
        box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.25) !important;
    }

    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="select"] > div:focus,
    div[data-baseweb="select"] > div:active,
    div[data-baseweb="select"] [role="button"]:focus,
    .stSelectbox > div > div:focus-within,
    .stSelectbox:focus-within {
        border-color: #1976D2 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-baseweb="slider"] [role="slider"] {
        background-color: #D32F2F !important;
    }

    /* Chat input FOCUS - Override red with blue */
    section[data-testid="stChatInput"]:focus-within,
    section[data-testid="stChatInput"] > div:focus-within,
    section[data-testid="stChatInput"] div:focus-within,
    section[data-testid="stChatInput"] textarea:focus,
    section[data-testid="stChatInput"] textarea:focus-visible,
    section[data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within,
    section[data-testid="stChatInput"] [data-baseweb="input"]:focus-within,
    section[data-testid="stChatInput"] [data-baseweb="base-input"]:focus-within {
        border-color: #1976D2 !important;
        box-shadow: #1976D2 0px 0px 0px 1px !important;
        outline: none !important;
    }

    div[data-baseweb="slider"] > div > div {
        background-color: #FFCDD2 !important;
    }

    button[kind="primary"] {
        background-color: #D32F2F !important;
        color: white !important;
        border: 1px solid #D32F2F !important;
    }
    button[kind="primary"]:hover {
        background-color: #B71C1C !important;
        border: 1px solid #B71C1C !important;
    }

    .stChatInputContainer textarea:focus,
    .stChatInputContainer textarea:focus-visible,
    textarea[aria-label*="Ask a question"]:focus,
    textarea[aria-label*="Ask a question"]:focus-visible {
        border-color: #1976D2 !important;
        box-shadow: 0 0 0 0.2rem rgba(25, 118, 210, 0.25) !important;
        outline: none !important;
    }

    /* Audio recorder styling */
    .stAudio {
        border-radius: 8px;
        padding: 4px;
    }

    /* Make audio player compact */
    audio {
        max-width: 100%;
        height: 40px;
    }

    /* Style for audio captions */
    .stCaptionContainer {
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }

    /* Chat input container alignment */
    .chat-input-container {
        display: flex;
        align-items: flex-end;
        gap: 0.5rem;
    }

    /* Align audio recorder button with chat input */
    .chat-input-container > div {
        display: flex;
        align-items: flex-end;
    }

    /* Audio recorder button positioning */
    .chat-input-container button[title="Record"] {
        margin-bottom: 0.5rem;
    }

    /* Hide selected option in selectbox dropdown */
    div[data-baseweb="select"] ul[role="listbox"] li[aria-selected="true"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

initialize_session_state()

with st.sidebar:
    st.header("Configuration")

    # App Selector
    app_mode = st.selectbox(
        "Select App",
        ["📰 News", "🎥 YouTube", "📄 PDF Documents"],
        format_func=lambda x: x,
        help="Choose between News Articles, YouTube Videos, or PDF Documents"
    )

    # Clear chat history when switching apps
    if st.session_state.current_app_mode != app_mode:
        st.session_state.chat_history = []
        st.session_state.processing_message = False
        st.session_state.current_app_mode = app_mode

    st.divider()

    st.subheader("LLM Provider")
    provider = st.selectbox(
        "Select Provider",
        ["openai", "groq"],
        format_func=lambda x: x.upper(),
        help="Choose between OpenAI and Groq"
    )

    st.subheader("API Keys")
    api_key = st.text_input(
        f"{provider.upper()} API Key",
        type="password",
        key=f"{provider}_key"
    ) or (env_config.openai_api_key if provider == "openai" else env_config.groq_api_key)

    if not api_key:
        st.warning(f"⚠️ Please provide your {provider.upper()} API key")

    # ElevenLabs API key for text-to-speech
    elevenlabs_key = st.text_input(
        "ElevenLabs API Key (Optional)",
        type="password",
        key="elevenlabs_key",
        help="Required for speech mode (text-to-speech)"
    ) or env_config.elevenlabs_api_key

    # Initialize speech service if we have the necessary keys
    if api_key and (provider == "openai" or env_config.openai_api_key):
        openai_key_for_speech = api_key if provider == "openai" else env_config.openai_api_key
        try:
            if elevenlabs_key:
                st.session_state.speech_service = SpeechService(
                    openai_api_key=openai_key_for_speech,
                    elevenlabs_api_key=elevenlabs_key
                )
            elif openai_key_for_speech:
                # Initialize with just OpenAI for STT (no TTS)
                st.session_state.speech_service = SpeechService(
                    openai_api_key=openai_key_for_speech,
                    elevenlabs_api_key=None
                )
        except Exception as e:
            st.session_state.speech_service = None

    st.subheader("Model Selection")
    model = st.selectbox(
        "Select Model",
        LLMProviderFactory.get_models_for_provider(provider),
        help=f"Choose the {provider.upper()} model for summarization"
    )

    st.subheader("Embedding Model")
    embedding_display_names = EmbeddingModel.get_display_names()
    embedding_choice = st.selectbox(
        "Select Embedding",
        list(embedding_display_names.keys()),
        format_func=lambda x: embedding_display_names[x],
        help="Embedding model for RAG mode"
    )

    if embedding_choice == "openai" and (provider != "openai" or not api_key):
        st.warning("⚠️ OpenAI API key required for OpenAI embeddings")

    st.subheader("Generation Parameters")
    temperature = st.slider(
        "Temperature",
        0.0,
        1.0,
        0.3,
        0.1,
        help="Controls randomness. Lower = more focused, Higher = more creative")
    max_tokens = st.slider("Max Tokens", 256, 4096, 1024, 256,
                           help="Maximum length of the generated response")

    st.divider()

    if st.button(
        "Clear Index",
        type="primary",
        use_container_width=True,
            help="⚠️ This will permanently delete all indexed articles from the vector database"):
        if st.session_state.rag_system:
            st.session_state.rag_system.clear_collection()
            st.session_state.indexed_urls = []
            st.success("Index cleared!")
            st.rerun()

# Main content area
if app_mode == "📰 News":
    st.title("📰 News Article Summarizer")

    mode = st.radio(
        "Choose Mode:",
        ["🚀 Quick Summarize", "🔍 RAG Mode (Index & Query)"],
        index=1,  # Default to RAG Mode
        horizontal=True,
        help=f"Quick Summarize: Direct article summarization | RAG Mode: Index multiple articles and query across them using vector search and summarize using {model}"
    )

    if mode == "🚀 Quick Summarize":
        st.markdown(
            f"**Article summarization using {provider.upper()} {model}**")

        quick_url = st.text_input(
            "Enter News Article URL",
            placeholder="https://www.bbc.com/news/article...",
            key="quick_url"
        )

        summary_type = st.selectbox(
            "Summary Type",
            ["detailed", "concise"],
            help="Detailed: Comprehensive summary | Concise: Brief overview"
        )

        listen_to_summary = st.checkbox(
            "🔊 Listen to summary",
            value=False,
            help="Generate audio narration of the summary using ElevenLabs TTS",
            disabled=not (st.session_state.speech_service and st.session_state.speech_service.elevenlabs_client),
            key="listen_news_quick"
        )

        if st.button("📝 Summarize Article", type="secondary"):
            if not quick_url:
                st.warning("Please enter a URL")
            elif not api_key:
                st.error(
                    f"⚠️ {
                        provider.upper()} API key required. Please add it in the sidebar.")
            else:
                with st.spinner("Fetching and summarizing article..."):
                    try:
                        summarizer = NewsArticleSummarizer(
                            provider=provider,
                            model_name=model,
                            api_key=api_key,
                            temperature=temperature
                        )

                        result = summarizer.summarize(
                            quick_url, summary_type=summary_type)

                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            st.success("✅ Summary Generated!")

                            st.markdown(f"### 📰 {result['title']}")
                            if result['authors']:
                                st.caption(
                                    f"**Authors:** {', '.join(result['authors'])}")
                            if result['publish_date']:
                                st.caption(
                                    f"**Published:** {result['publish_date']}")
                            st.caption(
                                f"**Source:** [{quick_url}]({quick_url})")

                            st.divider()

                            st.markdown("### 📝 Summary")
                            summary_text = result['summary'].get('output_text', str(result['summary']))
                            st.markdown(summary_text)

                            # Generate audio if requested
                            if listen_to_summary and st.session_state.speech_service:
                                with st.spinner("🔊 Generating audio..."):
                                    audio_bytes = st.session_state.speech_service.generate_speech(summary_text)
                                    if audio_bytes:
                                        st.audio(audio_bytes, format="audio/mpeg")
                                    else:
                                        st.warning("⚠️ Failed to generate audio. Please check your ElevenLabs API key.")

                            st.divider()

                            st.caption(
                                f"**Provider:** {result['model_info']['provider'].upper()}")
                            st.caption(
                                f"**Model:** {result['model_info']['name']}")
                            st.caption(f"**Summary Type:** {summary_type}")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)

    else:
        st.markdown(
            f"**Index multiple articles and query across them using vector search and summarize using {
                provider.upper()} {model}**")

        try:
            needs_init = (
                st.session_state.rag_system is None or
                st.session_state.current_embedding != embedding_choice or
                st.session_state.current_model != model or
                st.session_state.current_collection != "news_articles"
            )

            if needs_init:
                if not api_key:
                    st.warning(
                        f"⚠️ Please provide your {
                            provider.upper()} API key in the sidebar.")
                    st.stop()

                if embedding_choice == "openai" and provider != "openai":
                    st.warning(
                        "⚠️ OpenAI embeddings require OpenAI API key. Please select a different embedding or provider.")
                    st.stop()

                with st.spinner("Initializing RAG system..."):
                    st.session_state.rag_system = initialize_rag_system(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        temperature=temperature,
                        embedding_choice=embedding_choice,
                        collection_name="news_articles"
                    )
                    st.session_state.current_embedding = embedding_choice
                    st.session_state.current_model = model
                    st.session_state.current_collection = "news_articles"

        except Exception as e:
            st.error(f"Failed to initialize RAG system: {str(e)}")
            st.stop()

        st.divider()

        st.subheader("RAG Operations")

        rag_mode = st.radio(
            "Select Operation:",
            [MODE_CHAT, MODE_INDEX, MODE_VIEW],
            horizontal=True,
            help="Chat: Have conversations about indexed articles | Index: Add new articles | View: See and delete articles"
        )

        if rag_mode == MODE_INDEX:
            st.markdown("**Add new articles to the vector store**")

            bulk_urls = st.text_area(
                "Enter Article URLs (one per line)",
                placeholder="https://example.com/article1\nhttps://example.com/article2",
                height=100,
                help="Enter multiple URLs, one per line")

            if st.button("Index All", type="secondary"):
                if not bulk_urls:
                    st.warning("Please enter at least one URL")
                else:
                    urls = [url.strip()
                            for url in bulk_urls.split("\n") if url.strip()]

                    if urls:
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        success_count = 0
                        for i, url in enumerate(urls):
                            status_text.text(
                                f"Indexing {i + 1}/{len(urls)}: {url[:50]}...")
                            result = st.session_state.rag_system.index_url(url)

                            if result["success"]:
                                success_count += 1
                                if url not in st.session_state.indexed_urls:
                                    st.session_state.indexed_urls.append(url)

                            progress_bar.progress((i + 1) / len(urls))

                        status_text.empty()
                        progress_bar.empty()

                        if success_count == len(urls):
                            st.success(
                                f"✅ Successfully indexed all {success_count} articles!")
                        elif success_count > 0:
                            st.warning(
                                f"⚠️ Indexed {success_count}/{len(urls)} articles. Some failed.")
                        else:
                            st.error("❌ Failed to index any articles")

        elif rag_mode == MODE_VIEW:
            render_view_indexed(content_type="news")

        else:  # Chat Mode
            render_chat_interface(content_type="news")

elif app_mode == "🎥 YouTube":
    # YOUTUBE MODE
    st.title("🎥 YouTube Video Summarizer")

    mode = st.radio(
        "Choose Mode:",
        ["🚀 Quick Summarize", "🔍 RAG Mode (Index & Query)"],
        index=1,  # Default to RAG Mode
        horizontal=True,
        help=f"Quick Summarize: Direct video summarization | RAG Mode: Index multiple videos and query across them using vector search and summarize using {model}"
    )

    if mode == "🚀 Quick Summarize":
        st.markdown(
            f"**Video summarization using {provider.upper()} {model}**")

        quick_url = st.text_input(
            "Enter YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="quick_yt_url"
        )

        summary_type = st.selectbox(
            "Summary Type",
            ["detailed", "concise"],
            help="Detailed: Comprehensive summary | Concise: Brief overview"
        )

        listen_to_summary = st.checkbox(
            "🔊 Listen to summary",
            value=False,
            help="Generate audio narration of the summary using ElevenLabs TTS",
            disabled=not (st.session_state.speech_service and st.session_state.speech_service.elevenlabs_client),
            key="listen_youtube_quick"
        )

        if st.button("📝 Summarize Video", type="secondary"):
            if not quick_url:
                st.warning("Please enter a YouTube URL")
            elif not api_key:
                st.error(
                    f"⚠️ {
                        provider.upper()} API key required. Please add it in the sidebar.")
            else:
                with st.spinner("Downloading and transcribing video... This may take several minutes."):
                    try:
                        summarizer = YouTubeVideoSummarizer(
                            provider=provider,
                            model_name=model,
                            api_key=api_key,
                            temperature=temperature,
                            whisper_model="base"
                        )

                        result = summarizer.summarize(
                            quick_url, summary_type=summary_type)

                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            st.success("✅ Summary Generated!")

                            st.markdown(f"### 🎥 {result['title']}")
                            st.caption(
                                f"**Channel:** {result['author']}")
                            st.caption(
                                f"**Duration:** {result['duration_str']}")
                            st.caption(
                                f"**Uploaded:** {result['upload_date']}")
                            st.caption(
                                f"**Source:** [{quick_url}]({quick_url})")

                            st.divider()

                            st.markdown("### 📝 Summary")
                            summary_text = result['summary'].get('output_text', str(result['summary']))
                            st.markdown(summary_text)

                            # Generate audio if requested
                            if listen_to_summary and st.session_state.speech_service:
                                with st.spinner("🔊 Generating audio..."):
                                    audio_bytes = st.session_state.speech_service.generate_speech(summary_text)
                                    if audio_bytes:
                                        st.audio(audio_bytes, format="audio/mpeg")
                                    else:
                                        st.warning("⚠️ Failed to generate audio. Please check your ElevenLabs API key.")

                            st.divider()

                            st.caption(
                                f"**Provider:** {result['model_info']['provider'].upper()}")
                            st.caption(
                                f"**Model:** {result['model_info']['name']}")
                            st.caption(f"**Summary Type:** {summary_type}")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)

    else:
        st.markdown(
            f"**Index multiple videos and query across them using vector search and summarize using {
                provider.upper()} {model}**")

        try:
            needs_init = (
                st.session_state.rag_system is None or
                st.session_state.current_embedding != embedding_choice or
                st.session_state.current_model != model or
                st.session_state.current_collection != "youtube_videos"
            )

            if needs_init:
                if not api_key:
                    st.warning(
                        f"⚠️ Please provide your {
                            provider.upper()} API key in the sidebar.")
                    st.stop()

                if embedding_choice == "openai" and provider != "openai":
                    st.warning(
                        "⚠️ OpenAI embeddings require OpenAI API key. Please select a different embedding or provider.")
                    st.stop()

                with st.spinner("Initializing RAG system..."):
                    st.session_state.rag_system = initialize_rag_system(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        temperature=temperature,
                        embedding_choice=embedding_choice,
                        collection_name="youtube_videos"
                    )
                    st.session_state.current_embedding = embedding_choice
                    st.session_state.current_model = model
                    st.session_state.current_collection = "youtube_videos"

        except Exception as e:
            st.error(f"Failed to initialize RAG system: {str(e)}")
            st.stop()

        st.divider()

        st.subheader("YouTube Operations")

        yt_mode = st.radio(
            "Select Operation:",
            [MODE_CHAT, "📹 Index Videos", MODE_VIEW],
            horizontal=True,
            help="Chat: Have conversations about indexed videos | Index: Add new videos | View: See and delete videos"
        )

        if yt_mode == "📹 Index Videos":
            st.markdown("**Add YouTube videos to the vector store**")

            st.info(
                "⏱️ Note: Processing videos takes time (download + transcription). Please be patient!")

            video_url = st.text_input(
                "Enter YouTube Video URL",
                placeholder="https://www.youtube.com/watch?v=...",
                key="yt_url"
            )

            if st.button("Index Video", type="secondary"):
                if not video_url:
                    st.warning("Please enter a YouTube URL")
                else:
                    with st.spinner("Downloading and transcribing video... This may take several minutes."):
                        result = st.session_state.rag_system.index_youtube_url(
                            video_url)

                        if result["success"]:
                            st.success(
                                f"✅ Successfully indexed video: {
                                    result['title']}")
                            st.info(
                                f"📊 Created {
                                    result['num_chunks']} chunks | ⏱️ Duration: {
                                    result.get(
                                        'duration',
                                        'Unknown')}s | 👤 Author: {
                                    result.get(
                                        'author',
                                        'Unknown')}")
                            if video_url not in st.session_state.indexed_urls:
                                st.session_state.indexed_urls.append(video_url)
                        else:
                            st.error(f"❌ {result['message']}")

        elif yt_mode == MODE_VIEW:
            render_view_indexed(content_type="youtube")

        else:  # Chat Mode
            render_chat_interface(content_type="youtube")

else:
    # PDF DOCUMENTS MODE
    st.title("📄 PDF Document Summarizer")

    mode = st.radio(
        "Choose Mode:",
        ["🚀 Quick Summarize", "🔍 RAG Mode (Index & Query)"],
        index=1,
        horizontal=True,
        help=f"Quick Summarize: Direct PDF summarization | RAG Mode: Index multiple PDFs and query across them using vector search and summarize using {model}"
    )

    if mode == "🚀 Quick Summarize":
        st.markdown(f"**PDF summarization using {provider.upper()} {model}**")

        uploaded_file = st.file_uploader(
            "Upload PDF Document",
            type=["pdf"],
            help="Upload a PDF file to summarize",
            key="quick_pdf"
        )

        summary_type = st.selectbox(
            "Summary Type",
            ["detailed", "concise"],
            help="Detailed: Comprehensive summary | Concise: Brief overview"
        )

        listen_to_summary = st.checkbox(
            "🔊 Listen to summary",
            value=False,
            help="Generate audio narration of the summary using ElevenLabs TTS",
            disabled=not (st.session_state.speech_service and st.session_state.speech_service.elevenlabs_client),
            key="listen_pdf_quick"
        )

        if st.button("📝 Summarize PDF", type="secondary"):
            if not uploaded_file:
                st.warning("Please upload a PDF file")
            elif not api_key:
                st.error(f"⚠️ {provider.upper()} API key required. Please add it in the sidebar.")
            else:
                with st.spinner("Processing PDF..."):
                    try:
                        pdf_summarizer = PDFSummarizer(
                            provider=provider,
                            model_name=model,
                            api_key=api_key,
                            temperature=temperature
                        )

                        pdf_bytes = uploaded_file.read()
                        result = pdf_summarizer.summarize_from_bytes(pdf_bytes, uploaded_file.name, summary_type=summary_type)

                        if result.get("error"):
                            st.error(f"❌ {result.get('error', 'Unknown error')}")
                        else:
                            st.success("✅ Summary Generated!")

                            st.markdown(f"### 📄 {result['filename']}")
                            st.caption(f"**Pages:** {result['num_pages']}")

                            st.divider()

                            st.markdown("### 📝 Summary")
                            summary_text = result['summary']['output_text']
                            st.markdown(summary_text)

                            # Generate audio if requested
                            if listen_to_summary and st.session_state.speech_service:
                                with st.spinner("🔊 Generating audio..."):
                                    audio_bytes = st.session_state.speech_service.generate_speech(summary_text)
                                    if audio_bytes:
                                        st.audio(audio_bytes, format="audio/mpeg")
                                    else:
                                        st.warning("⚠️ Failed to generate audio. Please check your ElevenLabs API key.")

                            st.divider()

                            st.caption(f"**Provider:** {result['model_info']['provider'].upper()}")
                            st.caption(f"**Model:** {result['model_info']['name']}")
                            st.caption(f"**Summary Type:** {summary_type}")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    else:
        st.markdown(f"**Index multiple PDFs and query across them using vector search and summarize using {provider.upper()} {model}**")

        try:
            needs_init = (
                st.session_state.rag_system is None or
                st.session_state.current_embedding != embedding_choice or
                st.session_state.current_model != model or
                st.session_state.current_collection != "pdf_documents"
            )

            if needs_init:
                if not api_key:
                    st.warning(f"⚠️ Please provide your {provider.upper()} API key in the sidebar.")
                    st.stop()

                if embedding_choice == "openai" and provider != "openai":
                    st.warning("⚠️ OpenAI embeddings require OpenAI API key. Please select a different embedding or provider.")
                    st.stop()

                with st.spinner("Initializing RAG system..."):
                    st.session_state.rag_system = initialize_rag_system(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        temperature=temperature,
                        embedding_choice=embedding_choice,
                        collection_name="pdf_documents"
                    )
                    st.session_state.current_embedding = embedding_choice
                    st.session_state.current_model = model
                    st.session_state.current_collection = "pdf_documents"

        except Exception as e:
            st.error(f"Failed to initialize RAG system: {str(e)}")
            st.stop()

        st.divider()

        st.subheader("PDF Operations")

        pdf_mode = st.radio(
            "Select Operation:",
            [MODE_CHAT, "📄 Index PDFs", MODE_VIEW],
            horizontal=True,
            help="Chat: Have conversations about indexed PDFs | Index: Add new PDFs | View: See and delete PDFs"
        )

        if pdf_mode == "📄 Index PDFs":
            st.markdown("**Upload and index PDF documents**")

            uploaded_files = st.file_uploader(
                "Upload PDF Documents",
                type=["pdf"],
                accept_multiple_files=True,
                help="Upload one or more PDF files to index",
                key="pdf_uploader"
            )

            if st.button("Index All PDFs", type="secondary"):
                if not uploaded_files:
                    st.warning("Please upload at least one PDF file")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    success_count = 0
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing {i + 1}/{len(uploaded_files)}: {uploaded_file.name}...")

                        try:
                            pdf_bytes = uploaded_file.read()
                            index_result = st.session_state.rag_system.index_pdf(
                                pdf_bytes,
                                uploaded_file.name
                            )

                            if index_result["success"]:
                                success_count += 1
                                if uploaded_file.name not in st.session_state.indexed_urls:
                                    st.session_state.indexed_urls.append(uploaded_file.name)

                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {str(e)}")

                        progress_bar.progress((i + 1) / len(uploaded_files))

                    status_text.empty()
                    progress_bar.empty()

                    if success_count == len(uploaded_files):
                        st.success(f"✅ Successfully indexed all {success_count} PDFs!")
                    elif success_count > 0:
                        st.warning(f"⚠️ Indexed {success_count}/{len(uploaded_files)} PDFs. Some failed.")
                    else:
                        st.error("❌ Failed to index any PDFs")

        elif pdf_mode == MODE_VIEW:
            render_view_indexed(content_type="pdf")

        else:  # Chat Mode
            render_chat_interface(content_type="pdf")
