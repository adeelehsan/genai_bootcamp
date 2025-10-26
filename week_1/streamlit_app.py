import streamlit as st
from main import LLMApp
from appconfig import CHATBOT_NAME, env_config

st.set_page_config(
    page_title=f"{CHATBOT_NAME}",
    page_icon="🤖",
    layout="centered"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm_app" not in st.session_state:
    st.session_state.llm_app = None
if "current_model" not in st.session_state:
    st.session_state.current_model = None

st.title(CHATBOT_NAME)

with st.sidebar:
    st.header("Configuration")

    st.subheader("API Keys")
    groq_api_key = st.text_input("Groq API Key", type="password") or env_config.groq_api_key
    openai_api_key = st.text_input("OpenAI API Key", type="password") or env_config.openai_api_key

    st.subheader("Model")
    model = st.selectbox(
        "Select Model",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
        ]
    )

    is_gpt5 = any(gpt in model.lower() for gpt in ["gpt-5"])
    if is_gpt5 and not openai_api_key:
        st.warning("⚠️ OpenAI API key required for this model")
    elif not is_gpt5 and not groq_api_key:
        st.warning("⚠️ Groq API key required for this model")

    st.subheader("Parameters")

    is_gpt5 = any(gpt in model.lower() for gpt in ["gpt-5"])

    if is_gpt5:
        st.info("ℹ️ GPT-5 models use fixed temperature (1.0)")
        temperature = 1.0
    else:
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

    max_tokens = st.slider("Max Tokens", 256, 4096, 1024, 256)

    st.subheader("System Prompt")
    system_prompt = st.text_area(
        "Custom Instructions (Optional)",
        placeholder="Leave empty to use default prompt..."
    )

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Message"):
    is_gpt5 = any(gpt in model.lower() for gpt in ["gpt-5"])

    if (is_gpt5 and not openai_api_key) or (not is_gpt5 and not groq_api_key):
        st.stop()
    else:
        if st.session_state.llm_app is None or st.session_state.current_model != model:
            try:
                st.session_state.llm_app = LLMApp(
                    api_key=groq_api_key,
                    openai_api_key=openai_api_key,
                    model=model
                )
                st.session_state.current_model = model
            except Exception as e:
                st.error(f"Initialization error: {str(e)}")
                st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.llm_app.chat(
                        user_message=prompt,
                        system_prompt=system_prompt if system_prompt else None,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {str(e)}")
