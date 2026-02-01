"""
rag.py

This file contains the "core logic" of the chatbot:
- connect to ChromaDB
- embed a user query
- retrieve the most relevant chunks
- call LM Studio (OpenAI-like REST API) to generate the final answer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import requests

import chromadb
from sentence_transformers import SentenceTransformer


@dataclass
class Settings:
    """
    All tunable parameters in one place.
    This makes the app easier to understand and maintain.
    """
    lm_base_url: str
    model_id: str
    temperature: float = 0.2
    top_k: int = 3
    collection_name: str = "othello"
    chroma_dir: str = "chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


def get_collection(s: Settings):
    """Load the ChromaDB collection that stores Othello chunks."""
    client = chromadb.PersistentClient(path=s.chroma_dir)
    return client.get_or_create_collection(name=s.collection_name)


def get_embedder(s: Settings) -> SentenceTransformer:
    """Load the embedding model (used both at build time and query time)."""
    return SentenceTransformer(s.embedding_model)


def embed_text(embedder: SentenceTransformer, text: str) -> List[float]:
    """Convert text into a normalized embedding vector."""
    return embedder.encode([text], normalize_embeddings=True)[0].tolist()


def retrieve(col, query_emb: List[float], top_k: int) -> List[Tuple[str, Dict]]:
    """
    Retrieve top-k most similar chunks from ChromaDB.

    Returns a list of (chunk_text, metadata).
    """
    res = col.query(query_embeddings=[query_emb], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    return list(zip(docs, metas))


def format_context(chunks: List[Tuple[str, Dict]]) -> Tuple[str, List[str]]:
    """
    Build a context block + human-readable citations.

    We add [S1], [S2] ... markers so the answer can cite sources.
    """
    ctx_lines: List[str] = []
    cites: List[str] = []
    for i, (txt, meta) in enumerate(chunks, start=1):
        marker = f"S{i}"
        ctx_lines.append(f"[{marker}] {txt}")
        cites.append(f"[{marker}] source={meta.get('source')} chunk_id={meta.get('chunk_id')}")
    return "\n\n".join(ctx_lines), cites


def lmstudio_chat(s: Settings, messages: List[Dict]) -> str:
    """
    Call LM Studio like an OpenAI-compatible API.

    Endpoint: POST /v1/chat/completions
    """
    url = f"{s.lm_base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": s.model_id,
        "messages": messages,
        "temperature": s.temperature,
        "max_tokens": 400,
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def answer_with_rag(s: Settings, question: str, history: List[Dict]) -> Tuple[str, List[str]]:
    """
    End-to-end RAG:
    1) embed question
    2) retrieve top-k chunks
    3) send augmented prompt to the LLM
    4) return answer + citations list
    """
    col = get_collection(s)
    embedder = get_embedder(s)

    q_emb = embed_text(embedder, question)
    chunks = retrieve(col, q_emb, s.top_k)
    context, citations = format_context(chunks)

    system = {
        "role": "system",
        "content": (
            "You are a helpful assistant for questions about Shakespeare's Othello. "
            "Use ONLY the provided context when possible. "
            "When you use a chunk, cite it with [S1], [S2], etc. "
            "If the context is not enough, say what is missing."
        ),
    }
    user = {
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer with citations.",
    }
    messages = [system] + history + [user]
    return lmstudio_chat(s, messages), citations
