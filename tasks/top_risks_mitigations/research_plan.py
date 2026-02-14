from __future__ import annotations

from retrieval.retriever import search_docs
from retrieval.research_utils import dedupe_results_keep_order

def retrieve_top_risks(query: str) -> list[dict]:
    results = []
    results += search_docs(query, top_k=12, overfetch=80)
    results += search_docs("risk blocker mitigation risks register", top_k=10, overfetch=80)
    return dedupe_results_keep_order(results)[:20]
