"""
app.py

Streamlit web app with 3 pages (as required):
- Home
- Chat
- Model Choice

We connect to LM Studio Local Server and allow the user
to choose between two locally downloaded models.
"""

from __future__ import annotations

from typing import Dict, List
import requests
import streamlit as st

from rag import Settings, answer_with_rag


DEFAULT_MODELS = [
    "mistralai/ministral-3-3b",
    "mistralai/mistral-7b-instruct-v0.3",
]


def init_state() -> None:
    """Initialize Streamlit session state once."""
    st.session_state.setdefault("lm_base_url", "http://127.0.0.1:1234")
    st.session_state.setdefault("model_id", DEFAULT_MODELS[0])
    st.session_state.setdefault("temperature", 0.2)
    st.session_state.setdefault("top_k", 3)
    st.session_state.setdefault("messages", [])  # chat history


def ping_lmstudio(base_url: str) -> bool:
    """Check if LM Studio server is reachable."""
    try:
        r = requests.get(f"{base_url.rstrip('/')}/v1/models", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def sidebar_controls() -> None:
    """
    Sidebar = widgets (course requires >= 3 widgets).
    We put configuration here to keep the chat page clean.
    """
    st.sidebar.header("LM Studio")
    st.session_state["lm_base_url"] = st.sidebar.text_input(
        "Base URL",
        value=st.session_state["lm_base_url"],
        help="LM Studio Local Server URL (Developer tab).",
    )

    ok = ping_lmstudio(st.session_state["lm_base_url"])
    st.sidebar.success("LM Studio connecté ✅" if ok else "LM Studio non connecté ❌")

    st.sidebar.header("RAG / génération")
    st.session_state["top_k"] = st.sidebar.slider("Top-K sources", 1, 8, st.session_state["top_k"])
    st.session_state["temperature"] = st.sidebar.slider("Température", 0.0, 1.0, st.session_state["temperature"])

    if st.sidebar.button("🧹 Reset chat"):
        st.session_state["messages"] = []


def page_home() -> None:
    """Homepage: present the project (required deliverable)."""
    st.title("Othello Chatbot (Streamlit + LM Studio + RAG)")
    st.write(
        "This app answers questions about *Othello* using:\n"
        "- A local LLM served by **LM Studio**\n"
        "- A **ChromaDB** vector database (RAG)\n"
        "- Source citations from retrieved chunks\n"
    )
    st.info("Go to **Model Choice** to pick your model, then **Chat** to ask questions.")


def page_model_choice() -> None:
    """Model Choice page (required)."""
    st.title("Model Choice")
    st.write("Choose which LM Studio model will answer your questions.")

    st.session_state["model_id"] = st.selectbox(
        "Model Identifier",
        options=DEFAULT_MODELS,
        index=DEFAULT_MODELS.index(st.session_state["model_id"]),
        help="These are the identifiers shown in LM Studio (Developer > Loaded Models).",
    )

    st.write("Current model:", f"`{st.session_state['model_id']}`")


def render_chat(messages: List[Dict]) -> None:
    """Display the conversation using Streamlit chat components."""
    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])


def history_for_llm(messages: List[Dict], max_turns: int = 6) -> List[Dict]:
    """
    Convert our stored chat into LLM-friendly history.

    We keep only the last few turns to avoid huge prompts.
    """
    trimmed = messages[-(max_turns * 2) :]
    return [{"role": m["role"], "content": m["content"]} for m in trimmed]


def page_chat() -> None:
    """Chat page (required). Must handle history + cite sources."""
    st.title("Chat")
    render_chat(st.session_state["messages"])

    question = st.chat_input("Ta question sur Othello…")
    if not question:
        return

    st.session_state["messages"].append({"role": "user", "content": question})

    s = Settings(
        lm_base_url=st.session_state["lm_base_url"],
        model_id=st.session_state["model_id"],
        temperature=float(st.session_state["temperature"]),
        top_k=int(st.session_state["top_k"]),
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            answer, cites = answer_with_rag(s, question, history_for_llm(st.session_state["messages"]))
        st.markdown(answer)
        with st.expander("Sources used"):
            for c in cites:
                st.write(c)

    st.session_state["messages"].append({"role": "assistant", "content": answer})


def main() -> None:
    """Main router: simple navigation between the 3 pages."""
    st.set_page_config(page_title="Othello Chatbot", layout="wide")
    init_state()
    sidebar_controls()

    page = st.sidebar.radio("Pages", ["Home", "Chat", "Model Choice"], index=1)
    if page == "Home":
        page_home()
    elif page == "Model Choice":
        page_model_choice()
    else:
        page_chat()


if __name__ == "__main__":
    main()
