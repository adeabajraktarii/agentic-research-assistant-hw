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
                json.dumps({"page_content": d.page_content, "metadata": d.metadata}, ensure_ascii=False)
                + "\n"
            )


def load_index() -> Tuple[FAISS, List[Document]]:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # NOTE: FAISS.load_local uses pickle under the hood for docstore/index metadata.
    # Keep data/index/ gitignored to avoid loading untrusted artifacts.
    vectorstore = FAISS.load_local(
        str(FAISS_PATH),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    chunk_docs: List[Document] = []
    if META_PATH.exists():
        with META_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                chunk_docs.append(Document(page_content=row["page_content"], metadata=row["metadata"]))

    return vectorstore, chunk_docs


def ensure_index(docs_dir: str = "data/docs", force_rebuild: bool = False) -> Tuple[FAISS, List[Document]]:
    faiss_files_ok = (FAISS_PATH / "index.faiss").exists() and (FAISS_PATH / "index.pkl").exists()
    meta_ok = META_PATH.exists()

    if not force_rebuild and faiss_files_ok and meta_ok:
        return load_index()

    vectorstore, chunks = build_faiss_index(docs_dir=docs_dir)
    save_index(vectorstore, chunks)
    return vectorstore, chunks
