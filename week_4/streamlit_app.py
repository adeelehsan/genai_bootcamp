"""Streamlit UI for AI Blog Generator."""

import streamlit as st
import os
from dotenv import load_dotenv
from src.graphs.graph_builder import GraphBuilder
from src.llms.openai_llm import OpenAILLM

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Blog Generator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Main styling */
    .main {
        padding: 2rem;
    }

    /* Title styling */
    h1 {
        color: #1E88E5;
        font-weight: 700;
    }

    /* Button styling */
    div.stButton > button {
        background-color: #1E88E5;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
    }

    div.stButton > button:hover {
        background-color: #1565C0;
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.3);
    }

    /* Input field focus */
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #1E88E5 !important;
        box-shadow: 0 0 0 0.2rem rgba(30, 136, 229, 0.25) !important;
    }

    /* Slider styling */
    .stSlider > div > div > div {
        background-color: #1E88E5;
    }

    /* Success message */
    .success-message {
        padding: 1rem;
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        border-radius: 4px;
        margin: 1rem 0;
    }

    /* Blog preview card */
    .blog-card {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #000000;
    }

    /* Sidebar text color */
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Sidebar headers */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }

    /* Sidebar input fields */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border-color: #333333 !important;
    }

    /* Sidebar dividers */
    section[data-testid="stSidebar"] hr {
        border-color: #333333 !important;
    }

    /* Sidebar metric values */
    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }

    /* Sidebar labels */
    section[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* Sidebar selectbox */
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: #1a1a1a !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        border-color: #333333 !important;
    }

    /* Info box */
    .stInfo {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }

    /* Warning box */
    .stWarning {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "generated_blogs" not in st.session_state:
    st.session_state.generated_blogs = []
if "current_blog" not in st.session_state:
    st.session_state.current_blog = None

# Supported languages with flags
SUPPORTED_LANGUAGES = {
    "English": "🇬🇧",
    "Spanish": "🇪🇸",
    "French": "🇫🇷",
    "German": "🇩🇪",
    "Italian": "🇮🇹",
    "Portuguese": "🇵🇹",
    "Chinese": "🇨🇳",
    "Japanese": "🇯🇵",
    "Korean": "🇰🇷",
    "Arabic": "🇸🇦",
    "Hindi": "🇮🇳",
    "Russian": "🇷🇺",
    "Dutch": "🇳🇱",
    "Turkish": "🇹🇷",
    "Polish": "🇵🇱",
}


def generate_blog(topic: str, model: str, temperature: float, api_key: str, language: str = "English"):
    """
    Generate a blog post using the LangGraph workflow.

    Args:
        topic: Blog topic
        model: OpenAI model to use
        temperature: Generation temperature
        api_key: OpenAI API key
        language: Target language for the blog

    Returns:
        dict: Generated blog or error
    """
    try:
        # Set API key temporarily
        os.environ["OPENAI_API_KEY"] = api_key

        # Initialize LLM
        openai_llm = OpenAILLM(model=model, temperature=temperature)
        llm = openai_llm.get_llm()

        # Build and execute graph
        graph_builder = GraphBuilder(llm)
        graph = graph_builder.setup_graph(usecase="topic")

        # Generate blog with language
        state = graph.invoke({"topic": topic, "language": language})

        # Check for errors
        if "error" in state and state["error"]:
            return {"success": False, "error": state["error"]}

        # Extract blog data
        blog = state.get("blog", {})

        return {
            "success": True,
            "topic": topic,
            "title": blog.get("title", ""),
            "content": blog.get("content", ""),
            "language": blog.get("language", language),
            "model": model,
            "temperature": temperature
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Configuration")

    st.markdown("### 🔑 API Settings")
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Enter your OpenAI API key"
    )

    if not openai_api_key:
        st.warning("⚠️ Please enter your OpenAI API key to continue")

    st.divider()

    st.markdown("### 🌍 Language Settings")
    language = st.selectbox(
        "Select Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: f"{SUPPORTED_LANGUAGES[x]} {x}",
        index=0,
        help="Choose the language for blog generation"
    )

    st.divider()

    st.markdown("### 🤖 Model Settings")
    model = st.selectbox(
        "Select Model",
        ["gpt-5", "gpt-5-mini"],
        index=1,
        help="Choose the OpenAI GPT-5 model for blog generation"
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Controls randomness. Lower = more focused, Higher = more creative"
    )

    st.divider()

    st.markdown("### 📊 Statistics")
    blog_count = len(st.session_state.generated_blogs)
    st.metric("Blogs Generated", blog_count)

    # Debug info (you can remove this later)
    if blog_count > 0:
        st.caption(f"📋 {blog_count} blog(s) in history")

    if st.session_state.generated_blogs:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.generated_blogs = []
            st.session_state.current_blog = None
            st.rerun()

    st.divider()

# Main content area
st.title("✍️ AI Blog Generator")
st.markdown("Generate professional, SEO-optimized blog posts in seconds using AI.")

# Create tabs
tab1, tab2 = st.tabs(["📝 Generate Blog", "📚 Blog History"])

with tab1:
    st.markdown("### Generate a New Blog Post")

    # Input form
    with st.form("blog_form"):
        topic = st.text_input(
            "Blog Topic",
            placeholder="e.g., Artificial Intelligence in Healthcare, Climate Change Solutions...",
            help="Enter the topic you want to generate a blog about"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.form_submit_button("🚀 Generate Blog", use_container_width=True)

    if submit_button:
        if not openai_api_key:
            st.error("❌ Please provide your OpenAI API key in the sidebar")
        elif not topic or len(topic.strip()) < 3:
            st.error("❌ Please enter a valid topic (at least 3 characters)")
        else:
            with st.spinner("🤖 Generating your blog post... This may take 30-60 seconds..."):
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text(f"📝 Creating blog title in {language}...")
                progress_bar.progress(30)

                # Generate blog with language
                result = generate_blog(topic, model, temperature, openai_api_key, language)

                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()

                if result["success"]:
                    # Store in session state
                    st.session_state.current_blog = result
                    st.session_state.generated_blogs.insert(0, result)

                    st.success(f"✅ Blog generated successfully! Total blogs: {len(st.session_state.generated_blogs)}")
                    st.balloons()
                else:
                    st.error(f"❌ Error: {result['error']}")

    # Display current blog
    if st.session_state.current_blog:
        st.divider()
        blog = st.session_state.current_blog

        # Blog header
        st.markdown(f"# {blog['title']}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"📌 Topic: {blog['topic']}")
        with col2:
            blog_lang = blog.get('language', 'English')
            lang_flag = SUPPORTED_LANGUAGES.get(blog_lang, "🌐")
            st.caption(f"{lang_flag} Language: {blog_lang}")
        with col3:
            st.caption(f"🤖 Model: {blog['model']}")
        with col4:
            st.caption(f"🌡️ Temperature: {blog['temperature']}")

        st.divider()

        # Blog content
        st.markdown(blog['content'])

        st.divider()

        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 6])

        with col1:
            st.download_button(
                label="📥 Download Markdown",
                data=f"# {blog['title']}\n\n{blog['content']}",
                file_name=f"{blog['topic'].replace(' ', '_').lower()}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with col2:
            st.download_button(
                label="📄 Download Text",
                data=f"{blog['title']}\n\n{blog['content']}",
                file_name=f"{blog['topic'].replace(' ', '_').lower()}.txt",
                mime="text/plain",
                use_container_width=True
            )

with tab2:
    st.markdown("### Previously Generated Blogs")

    if not st.session_state.generated_blogs:
        st.info("📭 No blogs generated yet. Create your first blog in the 'Generate Blog' tab!")
    else:
        for idx, blog in enumerate(st.session_state.generated_blogs):
            blog_lang = blog.get('language', 'English')
            lang_flag = SUPPORTED_LANGUAGES.get(blog_lang, "🌐")
            with st.expander(f"{lang_flag} {blog['title']}", expanded=(idx == 0)):
                st.markdown(f"**Topic:** {blog['topic']}")
                st.markdown(f"**Language:** {lang_flag} {blog_lang}")
                st.markdown(f"**Model:** {blog['model']} | **Temperature:** {blog['temperature']}")
                st.divider()
                st.markdown(blog['content'])

                col1, col2, col3 = st.columns([2, 2, 6])

                with col1:
                    st.download_button(
                        label="📥 Markdown",
                        data=f"# {blog['title']}\n\n{blog['content']}",
                        file_name=f"{blog['topic'].replace(' ', '_').lower()}_{idx}.md",
                        mime="text/markdown",
                        key=f"download_md_{idx}",
                        use_container_width=True
                    )

                with col2:
                    st.download_button(
                        label="📄 Text",
                        data=f"{blog['title']}\n\n{blog['content']}",
                        file_name=f"{blog['topic'].replace(' ', '_').lower()}_{idx}.txt",
                        mime="text/plain",
                        key=f"download_txt_{idx}",
                        use_container_width=True
                    )

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Built with ❤️ using LangGraph, OpenAI, and Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
