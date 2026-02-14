from __future__ import annotations
from retrieval.retriever import search_docs

def retrieve_default(query: str) -> list[dict]:
    return search_docs(query, top_k=8, overfetch=40)
