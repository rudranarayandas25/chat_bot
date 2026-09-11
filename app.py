import streamlit as st
from google import genai

# ---- Page config ----
st.set_page_config(page_title="My Chat App", page_icon="💬", layout="wide")
st.title("💬 Simple Chatbot")

# ---- Sidebar for settings ----
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Enter your Gemini API Key", type="password", value=st.session_state.get("api_key", ""))
    st.caption("Get a free key at aistudio.google.com/apikey — no credit card needed.")

    st.divider()

    model_name = st.selectbox(
        "Model",
        options=[
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
        ],
        index=0,
    )

    system_prompt = st.text_area(
        "System prompt",
        value="You are a helpful, friendly assistant.",
        height=100,
    )

    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max response length (tokens)", min_value=256, max_value=4096, value=1024, step=256)

    st.divider()

    if st.button("🗑️ Clear chat history", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! Ask me anything."}
        ]
        st.rerun()

# ---- Session state to store chat history ----
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask me anything."}
    ]

# ---- Display past messages ----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---- Chat input ----
user_input = st.chat_input("Type your message...")

if user_input:
    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar first.")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Build message history for the API (Gemini uses "model" instead of "assistant",
    # and excludes the initial greeting so it isn't treated as a prior conversation turn)
    history = []
    for m in st.session_state.messages[:-1]:  # everything except the message just sent
        if m["role"] == "assistant" and m["content"] == "Hi! Ask me anything.":
            continue
        role = "model" if m["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [m["content"]]})

    # ---- Call the Gemini API and stream the response ----
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        chat = model.start_chat(history=history)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            response_stream = chat.send_message(user_input, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        error_msg = f"⚠️ Something went wrong: {e}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        with st.chat_message("assistant"):
            st.error(error_msg)