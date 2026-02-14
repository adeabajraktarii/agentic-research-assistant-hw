from __future__ import annotations
from retrieval.retriever import search_docs

def retrieve_client_update_email(query: str) -> list[dict]:
    return search_docs(query, top_k=10, overfetch=60)
