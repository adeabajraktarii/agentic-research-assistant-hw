from __future__ import annotations

from shared_state import SharedState
from tasks.registry import get_research_plan


def _normalize_results_to_notes(results: list[dict]) -> list[dict]:
    """
    Convert retriever results -> SharedState.research_notes shape:
      [{"claim": <full chunk text>, "citations": [{"source_id","quote","location"}]}]
    """
    notes: list[dict] = []

    for r in results or []:
        content = (r.get("content") or "").strip()
        if not content:
            continue

        quote = content.replace("\n", " ").strip()
        if len(quote) > 260:
            quote = quote[:260] + "..."

        citation = {
            "source_id": (r.get("source_id") or "unknown_source").strip(),
            "quote": quote,
            "location": (r.get("locator") or "unknown location").strip(),
        }

        notes.append({"claim": content, "citations": [citation]})

    return notes


def _extract_query(state: SharedState) -> str:
    
    if isinstance(state.task_text, str) and state.task_text.strip():
        return state.task_text.strip()
    return (state.task or "").strip()


def researcher_agent(state: SharedState) -> SharedState:
    query = _extract_query(state)

    if not query:
        state.research_notes = [{
            "claim": "Not found in the sources.",
            "citations": []
        }]
        state.trace.append({
            "step": "research",
            "agent": "researcher",
            "action": "FAISS document retrieval",
            "outcome": "Failed: empty query",
        })
        return state

    plan = get_research_plan(state.task_key or "")

    try:
        results = plan.retrieve(query)
    except Exception as e:
        state.research_notes = [{
            "claim": "Not found in the sources.",
            "citations": []
        }]
        state.trace.append({
            "step": "research",
            "agent": "researcher",
            "action": plan.action_label,
            "outcome": f"Retrieval error: {type(e).__name__}: {str(e)[:160]}",
        })
        return state

    if not results:
        state.research_notes = [{
            "claim": "Not found in the sources.",
            "citations": []
        }]
        outcome = "No relevant documents retrieved"
    else:
        notes = _normalize_results_to_notes(results)
        if notes:
            state.research_notes = notes
            outcome = f"Retrieved {len(notes)} chunks"
        else:
            state.research_notes = [{
                "claim": "Not found in the sources.",
                "citations": []
            }]
            outcome = "Retrieved chunks but all were empty after normalization"

    # optional task-specific injection/postprocess (compare_approaches)
    if plan.postprocess:
        try:
            plan.postprocess(state)
        except Exception:
            
            pass

    state.meta["retrieval_debug"] = {
        "task_key": state.task_key,
        "query": query,
        "retrieved_count": len(state.research_notes),
        "action_label": plan.action_label,
        "has_postprocess": bool(plan.postprocess),
    }

    state.trace.append({
        "step": "research",
        "agent": "researcher",
        "action": plan.action_label,
        "outcome": outcome,
    })
    return state
