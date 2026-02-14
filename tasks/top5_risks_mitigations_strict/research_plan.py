from __future__ import annotations

from retrieval.retriever import search_docs
from retrieval.research_utils import dedupe_results_keep_order

def retrieve_top5_risks(query: str) -> list[dict]:
    boosted: list[dict] = []

    boosted += search_docs(query, top_k=18, must_include="risks.md", overfetch=120)

    boosted += search_docs(
        "Risks Register Severity Probability Impact Mitigation risks.md",
        top_k=12,
        must_include="risks.md",
        overfetch=120,
    )

    boosted += search_docs(
        "DB Migration Delay Vendor Credential Delay Security Review risks.md",
        top_k=12,
        must_include="risks.md",
        overfetch=120,
    )

    boosted += search_docs(
        "Onboarding Documentation Gaps Pricing Sensitivity Churn risks.md",
        top_k=12,
        must_include="risks.md",
        overfetch=120,
    )

    boosted += search_docs(
        "risk blocked vendor access integration tests security checklist",
        top_k=10,
        overfetch=80,
    )

    return dedupe_results_keep_order(boosted)[:30]
