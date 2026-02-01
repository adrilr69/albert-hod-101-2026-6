"""
build_vector_db.py

Goal
----
Build a local ChromaDB vector database for Othello:
- Download (or read) the book
- Chunk it into small pieces
- Embed each chunk
- Store (chunk_text + embedding + metadata) into ChromaDB

This script is a one-time (or occasional) preprocessing step.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import re
import requests

import chromadb
from sentence_transformers import SentenceTransformer


OTHELLO_URL = "https://www.gutenberg.org/cache/epub/2267/pg2267.txt"


@dataclass(frozen=True)
class BuildConfig:
    data_dir: Path = Path("data")
    chroma_dir: Path = Path("chroma_db")
    collection_name: str = "othello"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_words: int = 420
    overlap_words: int = 60


def ensure_data_dir(cfg: BuildConfig) -> None:
    """Create data directory if needed."""
    cfg.data_dir.mkdir(parents=True, exist_ok=True)


def fetch_othello_text(cfg: BuildConfig) -> str:
    """
    Return Othello raw text.

    We prefer a local file if it exists, otherwise we download it
    from Project Gutenberg (as required by the assignment).
    """
    ensure_data_dir(cfg)
    local_path = cfg.data_dir / "othello.txt"
    if local_path.exists():
        return local_path.read_text(encoding="utf-8", errors="ignore")

    resp = requests.get(OTHELLO_URL, timeout=60)
    resp.raise_for_status()
    local_path.write_text(resp.text, encoding="utf-8")
    return resp.text


def strip_gutenberg_boilerplate(text: str) -> str:
    """
    Remove Project Gutenberg header/footer to keep only the book content.

    This makes chunking more relevant (less noise).
    """
    start = re.search(r"\*\*\* START OF (THIS|THE) PROJECT GUTENBERG EBOOK", text)
    end = re.search(r"\*\*\* END OF (THIS|THE) PROJECT GUTENBERG EBOOK", text)
    if start and end:
        return text[start.end() : end.start()].strip()
    return text.strip()


def chunk_words(text: str, chunk_size: int, overlap: int) -> List[Tuple[int, str]]:
    """
    Split text into (chunk_id, chunk_text).

    We chunk by words because it is simple and robust.
    """
    words = text.split()
    out: List[Tuple[int, str]] = []
    step = max(1, chunk_size - overlap)
    chunk_id = 0
    for i in range(0, len(words), step):
        chunk = words[i : i + chunk_size]
        if len(chunk) < 50:
            break
        out.append((chunk_id, " ".join(chunk)))
        chunk_id += 1
    return out


def get_embedder(cfg: BuildConfig) -> SentenceTransformer:
    """Load the embedding model used to turn text into vectors."""
    return SentenceTransformer(cfg.embedding_model)


def get_collection(cfg: BuildConfig):
    """
    Create/load a persistent ChromaDB collection.

    The DB is stored on disk in cfg.chroma_dir.
    """
    client = chromadb.PersistentClient(path=str(cfg.chroma_dir))
    return client.get_or_create_collection(name=cfg.collection_name)


def upsert_chunks(col, chunks: List[Tuple[int, str]], emb_model: SentenceTransformer) -> None:
    """Compute embeddings and store them with metadata in ChromaDB."""
    ids = [f"chunk_{cid}" for cid, _ in chunks]
    docs = [txt for _, txt in chunks]
    embs = emb_model.encode(docs, normalize_embeddings=True).tolist()
    metas = [{"source": "Othello", "chunk_id": cid} for cid, _ in chunks]
    col.upsert(ids=ids, documents=docs, embeddings=embs, metadatas=metas)


def main() -> None:
    """Entry point: build the vector DB from scratch (idempotent upsert)."""
    cfg = BuildConfig()
    raw = fetch_othello_text(cfg)
    clean = strip_gutenberg_boilerplate(raw)
    chunks = chunk_words(clean, cfg.chunk_words, cfg.overlap_words)

    embedder = get_embedder(cfg)
    col = get_collection(cfg)
    upsert_chunks(col, chunks, embedder)

    print(f"✅ Stored {len(chunks)} chunks into ChromaDB: {cfg.chroma_dir}/{cfg.collection_name}")


if __name__ == "__main__":
    main()
