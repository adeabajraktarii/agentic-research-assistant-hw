from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from shared_state import SharedState


@dataclass(frozen=True)
class ResearchPlan:
    task_key: str
    action_label: str
    retrieve: Callable[[str], list[dict]]
    postprocess: Optional[Callable[[SharedState], None]] = None


def get_research_plan(task_key: str) -> ResearchPlan:
    key = (task_key or "").strip()

    if key == "compare_approaches":
        from tasks.compare_approaches.research_plan import retrieve_compare, postprocess_compare
        return ResearchPlan(
            task_key=key,
            action_label="FAISS retrieval (+forced technical_decisions.md + injected Option A/B anchor)",
            retrieve=retrieve_compare,
            postprocess=postprocess_compare,
        )

    if key == "top5_risks_mitigations_strict":
        from tasks.top5_risks_mitigations_strict.research_plan import retrieve_top5_risks
        return ResearchPlan(
            task_key=key,
            action_label="FAISS retrieval (boosted for risks.md)",
            retrieve=retrieve_top5_risks,
        )

    if key == "client_update_email":
        from tasks.client_update_email.research_plan import retrieve_client_update_email
        return ResearchPlan(
            task_key=key,
            action_label="FAISS retrieval (client update email)",
            retrieve=retrieve_client_update_email,
        )

    if key == "top_risks_mitigations":
        from tasks.top_risks_mitigations.research_plan import retrieve_top_risks
        return ResearchPlan(
            task_key=key,
            action_label="FAISS retrieval (top risks + mitigations)",
            retrieve=retrieve_top_risks,
        )

    if key == "extract_deadlines_and_owners":
        from tasks.extract_deadlines_and_owners.research_plan import retrieve_deadlines
        return ResearchPlan(
            task_key=key,
            action_label="FAISS retrieval (deadlines + owners)",
            retrieve=retrieve_deadlines,
        )

    if key == "draft_confluence_page":
        from tasks.draft_confluence_page.research_plan import retrieve_confluence
        return ResearchPlan(
            task_key=key,
            action_label="FAISS retrieval (confluence page)",
            retrieve=retrieve_confluence,
        )

    from tasks.default.research_plan import retrieve_default
    return ResearchPlan(
        task_key="default",
        action_label="FAISS retrieval",
        retrieve=retrieve_default,
    )
