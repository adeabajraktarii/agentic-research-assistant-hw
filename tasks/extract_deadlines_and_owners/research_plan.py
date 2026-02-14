from __future__ import annotations

from retrieval.retriever import search_docs
from retrieval.research_utils import dedupe_results_keep_order

def retrieve_deadlines(query: str) -> list[dict]:
    results = []
    results += search_docs(query, top_k=12, overfetch=80)
    results += search_docs("Owner Due Date Week action item status", top_k=12, overfetch=80)
    results += search_docs("deadline due by responsible owner", top_k=10, overfetch=80)
    return dedupe_results_keep_order(results)[:25]
