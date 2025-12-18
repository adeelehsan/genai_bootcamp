"""
Customer Support Chatbot - Streamlit UI
"""

import streamlit as st
from chatbot import CustomerSupportBot

# Page config
st.set_page_config(
    page_title="Customer Support",
    page_icon="🛒",
    layout="centered"
)

# Initialize session state
if "bot" not in st.session_state:
    st.session_state.bot = CustomerSupportBot()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

if "show_login" not in st.session_state:
    st.session_state.show_login = False

if "login_prompt_reason" not in st.session_state:
    st.session_state.login_prompt_reason = None


def do_login(email: str, pin: str):
    """Attempt to login with email and PIN."""
    try:
        result = st.session_state.bot.mcp.verify_customer_pin(email, pin)
        if "verified" in result.lower() or "Customer ID:" in result:
            # Parse customer info
            st.session_state.bot.session["authenticated"] = True
            st.session_state.bot.session["email"] = email
            lines = result.split("\n")
            for line in lines:
                if "Customer ID:" in line:
                    st.session_state.bot.session["customer_id"] = line.split("Customer ID:")[-1].strip()
                if "verified:" in line.lower():
                    # Extract name from "✓ Customer verified: Donald Garcia"
                    st.session_state.bot.session["customer_name"] = line.split(":")[-1].strip()
            return True, "Login successful!"
        else:
            return False, "Invalid email or PIN. Please try again."
    except Exception as e:
        return False, f"Login failed: {str(e)}"


def check_order_query(message: str) -> bool:
    """Check if message is asking about orders."""
    order_keywords = ["order", "orders", "purchase", "bought", "history", "tracking", "shipment", "delivery"]
    return any(keyword in message.lower() for keyword in order_keywords)


# Header
st.title("🛒 Customer Support")
st.caption("Ask me about products, orders, or anything else!")

# Show login status badge
if st.session_state.bot.session["authenticated"]:
    st.success(f"✅ Logged in as: {st.session_state.bot.session['customer_name']}")

# Sidebar
with st.sidebar:
    st.header("Account")

    if st.session_state.bot.session["authenticated"]:
        st.success(f"👤 {st.session_state.bot.session['customer_name']}")
        st.caption(f"📧 {st.session_state.bot.session['email']}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.bot.session = {
                "authenticated": False,
                "customer_id": None,
                "customer_name": None,
                "email": None
            }
            st.session_state.messages.append({
                "role": "assistant",
                "content": "You've been logged out. Let me know if you need anything!"
            })
            st.rerun()
    else:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.show_login = True
            st.session_state.login_prompt_reason = None
            st.rerun()

    st.divider()
    st.header("Browse Products")
    if st.button("🖥️ Computers", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Show me computers"})
        st.rerun()
    if st.button("🖵 Monitors", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Show me monitors"})
        st.rerun()
    if st.button("🖨️ Printers", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Show me printers"})
        st.rerun()
    if st.button("🎧 Accessories", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Show me accessories"})
        st.rerun()
    if st.button("🌐 Networking", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Show me networking products"})
        st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

# Login Modal
if st.session_state.show_login:
    with st.container():
        st.markdown("---")
        st.subheader("🔐 Login to Your Account")

        if st.session_state.login_prompt_reason:
            st.info(f"💡 {st.session_state.login_prompt_reason}")

        with st.form("login_form"):
            email = st.text_input("📧 Email Address", placeholder="your@email.com")
            pin = st.text_input("🔢 4-Digit PIN", type="password", max_chars=4, placeholder="****")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Login", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)

            if submit:
                if email and pin:
                    success, message = do_login(email, pin)
                    if success:
                        st.session_state.show_login = False
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Welcome back, {st.session_state.bot.session['customer_name']}! How can I help you today?"
                        })
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter both email and PIN")

            if cancel:
                st.session_state.show_login = False
                st.session_state.login_prompt_reason = None
                st.rerun()

        st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    # Check if asking about orders while not logged in
    if check_order_query(prompt) and not st.session_state.bot.session["authenticated"]:
        st.session_state.show_login = True
        st.session_state.login_prompt_reason = "Please login to view your orders"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({
            "role": "assistant",
            "content": "I'd be happy to help with your orders! Please login first using the form above. 👆"
        })
        st.rerun()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.bot.chat(prompt, st.session_state.history)
            st.markdown(response)

    # Update history for context
    st.session_state.history.append({"role": "user", "content": prompt})
    st.session_state.history.append({"role": "assistant", "content": response})

    # Keep history manageable (last 10 exchanges)
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[-20:]

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})

# Process any pending quick action messages
quick_actions = [
    "Show me computers", "Show me monitors", "Show me printers",
    "Show me accessories", "Show me networking products"
]
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_msg = st.session_state.messages[-1]["content"]
    if last_msg in quick_actions:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.bot.chat(last_msg, st.session_state.history)
                st.markdown(response)

        st.session_state.history.append({"role": "user", "content": last_msg})
        st.session_state.history.append({"role": "assistant", "content": response})
        st.session_state.messages.append({"role": "assistant", "content": response})
