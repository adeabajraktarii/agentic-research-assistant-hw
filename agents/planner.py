from __future__ import annotations

from shared_state import SharedState


def planner_agent(state: SharedState) -> SharedState:
    
    state.plan = [
        "Clarify the user goal + required outputs (deliverable package).",
        "Retrieve relevant evidence from provided documents.",
        "Draft deliverables strictly from evidence.",
        "Verify: check citations, missing evidence, contradictions. Enforce 'Not found in sources'.",
    ]

    state.trace.append({
        "step": "plan",
        "agent": "planner",
        "action": "Created execution plan for multi-agent workflow",
        "outcome": f"Plan created with {len(state.plan)} steps",
    })
    return state
