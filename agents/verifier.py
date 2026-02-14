from __future__ import annotations

from shared_state import SharedState


def _has_any_citations(notes: list[dict]) -> bool:
    for n in notes or []:
        cits = n.get("citations") if isinstance(n, dict) else None
        if isinstance(cits, list) and len(cits) > 0:
            return True
    return False


def verifier_agent(state: SharedState) -> SharedState:
    notes = state.research_notes or []
    problems: list[str] = []

    # Hard safety rule: no evidence -> no claims
    if not _has_any_citations(notes):
        problems.append("No citations found in research_notes. Output must be 'Not found in sources'.")

    state.verification_notes = problems

    if problems:
        state.final_output = (
            "## Deliverable Package\n\n"
            "### Executive Summary\n"
            "- Not found in sources.\n\n"
            "---\n"
            "## Verification\n"
            + "\n".join(f"- {p}" for p in problems)
        )
        outcome = f"Blocked final: {len(problems)} issue(s)"
    else:
        # Approve draft as final
        state.final_output = state.draft or ""
        # Add a small verification footer (transparent, minimal)
        state.final_output += (
            "\n\n---\n"
            "## Verification\n"
            "- Checked that at least one citation exists in retrieved evidence.\n"
        )
        outcome = "Final approved"

    state.trace.append({
        "step": "verify",
        "agent": "verifier",
        "action": "Checked minimum grounding (citations present) and enforced no-evidence rule",
        "outcome": outcome,
    })

    return state
