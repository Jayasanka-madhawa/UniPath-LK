import os
from pathlib import Path

import streamlit as st

# Ensure data paths resolve regardless of how Streamlit was launched.
os.chdir(Path(__file__).resolve().parent)

from src.agent.agent import run_agent
from src.agent.graph import reset_agent
from src.config import GOOGLE_MODEL, LLM_PROVIDER, OPENAI_MODEL

st.set_page_config(page_title="UniPath LK", page_icon="🎓", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = LLM_PROVIDER

EXAMPLES = [
    "My Z-score is 2.04 in Colombo. What courses can I get?",
    "Compare Physical Science vs Computer Science",
    "Can I apply if I registered at SLIATE?",
    "How do I change my Uni-Code preference order?",
]

PROVIDER_OPTIONS = ["ollama", "openai", "google"]
PROVIDER_LABELS = {
    "ollama": "Local (Ollama · llama3.2)",
    "openai": f"OpenAI (cloud · {OPENAI_MODEL})",
    "google": f"Google Gemini (cloud · {GOOGLE_MODEL})",
}


def _tool_calls_payload(result) -> list[dict]:
    return [
        {
            "action": call.action,
            "args": call.args,
            "observation": call.observation[:1000],
        }
        for call in result.tool_calls
    ]


def _generate_reply() -> None:
    with st.spinner("Thinking..."):
        result = run_agent(
            messages=st.session_state.messages,
            llm_provider=st.session_state.llm_provider,
        )
    assistant_message: dict = {
        "role": "assistant",
        "content": result.answer,
        "backend": result.backend,
    }
    if result.tool_calls:
        assistant_message["tool_calls"] = _tool_calls_payload(result)
    st.session_state.messages.append(assistant_message)


with st.sidebar:
    st.header("UniPath LK")
    st.markdown(
        "Ask about **courses**, **Z-scores**, **cutoffs**, and **UGC rules**. "
        "I'll look up the right information for you."
    )

    current = st.session_state.llm_provider
    if current not in PROVIDER_OPTIONS:
        current = "ollama"

    provider = st.selectbox(
        "AI model",
        options=PROVIDER_OPTIONS,
        index=PROVIDER_OPTIONS.index(current),
        format_func=lambda key: PROVIDER_LABELS[key],
    )
    if provider != st.session_state.llm_provider:
        st.session_state.llm_provider = provider
        reset_agent()
        st.rerun()

    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        st.error("Set `OPENAI_API_KEY` in `.env` to use OpenAI.")
    elif provider == "google" and not (
        os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    ):
        st.error("Set `GOOGLE_API_KEY` in `.env` to use Google Gemini.")
    elif provider == "ollama":
        st.caption("Requires Ollama running locally (`ollama serve`).")

    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Try asking:")
    for i, example in enumerate(EXAMPLES):
        if st.button(example, key=f"example_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": example})
            _generate_reply()
            st.rerun()

st.title("UniPath LK")
st.caption("UGC Sri Lanka admission assistant — grounded in the 2025/26 Student Handbook")

st.warning(
    "Educational demo only. Not official UGC advice. "
    "Always verify with [UGC Sri Lanka](https://www.ugc.ac.lk/)."
)

if not st.session_state.messages:
    st.info("Hi! Ask me about UGC admission, courses, Z-scores, or handbook rules.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("backend"):
            st.caption(f"Model: {message['backend']}")
        st.markdown(message["content"])
        tool_calls = message.get("tool_calls")
        if tool_calls:
            with st.expander("How I found this"):
                for call in tool_calls:
                    st.code(f"{call['action']}({call['args']})")
                    st.text(call.get("observation", ""))

if prompt := st.chat_input("Ask about courses, Z-scores, or UGC rules..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    _generate_reply()
    st.rerun()
