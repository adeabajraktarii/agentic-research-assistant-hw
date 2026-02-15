from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from retrieval.loader import load_and_chunk

load_dotenv()

INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

FAISS_PATH = INDEX_DIR / "faiss_index"
META_PATH = INDEX_DIR / "chunks_meta.jsonl"

EMBEDDING_MODEL = "text-embedding-3-small"


def build_faiss_index(docs_dir: str = "data/docs") -> Tuple[FAISS, List[Document]]:
    chunks = load_and_chunk(docs_dir=docs_dir)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore, chunks


def save_index(vectorstore: FAISS, chunk_docs: List[Document]) -> None:
    vectorstore.save_local(str(FAISS_PATH))

    with META_PATH.open("w", encoding="utf-8") as f:
        for d in chunk_docs:
            f.write(
                json.dumps(
                    {"page_content": d.page_content, "metadata": d.metadata},
                    ensure_ascii=False,
                )
                + "\n"
            )


def load_index() -> Tuple[FAISS, List[Document]]:
    """
    Load FAISS index in a Streamlit/Linux-safe way.
    If pickle fails (Windows vs Linux issue), rebuild index from docs.
    """
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    try:
        vectorstore = FAISS.load_local(
            str(FAISS_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception:
        # If loading fails (very common on Streamlit due to Windows pickle),
        # rebuild the index from documents.
        vectorstore, chunks = build_faiss_index()
        save_index(vectorstore, chunks)
        return vectorstore, chunks

    chunk_docs: List[Document] = []
    if META_PATH.exists():
        with META_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                chunk_docs.append(
                    Document(page_content=row["page_content"], metadata=row["metadata"])
                )

    return vectorstore, chunk_docs


def ensure_index(
    docs_dir: str = "data/docs", force_rebuild: bool = False
) -> Tuple[FAISS, List[Document]]:
    """
    Ensure index exists.
    IMPORTANT: We no longer require index.pkl (Windows pickle issue).
    If anything is missing or broken, we rebuild automatically.
    """

    faiss_exists = (FAISS_PATH / "index.faiss").exists()
    meta_ok = META_PATH.exists()

    if not force_rebuild and faiss_exists and meta_ok:
        return load_index()

    vectorstore, chunks = build_faiss_index(docs_dir=docs_dir)
    save_index(vectorstore, chunks)
    return vectorstore, chunks

