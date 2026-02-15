from __future__ import annotations

from shared_state import SharedState


def _has_any_citations(notes: list[dict]) -> bool:
    for n in notes or []:
        if not isinstance(n, dict):
            continue
        cits = n.get("citations")
        if isinstance(cits, list) and len(cits) > 0:
            return True
    return False


def _draft_has_citation_markers(text: str) -> bool:
    """
    We require the FINAL answer to show grounding markers (your system uses doc:...#chunk_...).
    This prevents generic answers (like pizza instructions) from passing.
    """
    if not text:
        return False
    # Common markers used across your project outputs
    markers = ["doc:", "#chunk_", "(doc:", "chunk "]
    return any(m in text for m in markers)


def verifier_agent(state: SharedState) -> SharedState:
    notes = state.research_notes or []
    draft = state.draft or ""
    problems: list[str] = []

    has_evidence = _has_any_citations(notes)
    draft_grounded = _draft_has_citation_markers(draft)

    # Rule 1: If retrieval has no citations, we must refuse.
    if not has_evidence:
        problems.append("No citations found in research_notes. Output must be 'Not found in sources'.")

    # Rule 2: Even if retrieval returned something, the answer itself must contain grounding markers.
    # This blocks generic, ungrounded responses for out-of-scope questions (e.g., pizza).
    if has_evidence and not draft_grounded:
        problems.append(
            "Draft contains no citation markers (e.g., doc:...#chunk_...). "
            "Answer appears ungrounded; must be 'Not found in sources'."
        )

    state.verification_notes = problems

    if problems:
        # IMPORTANT: wipe draft so the UI can't accidentally show it
        state.draft = ""

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
        state.final_output = draft + (
            "\n\n---\n"
            "## Verification\n"
            "- Checked that at least one citation exists in retrieved evidence.\n"
            "- Checked that the final answer includes citation markers.\n"
        )
        outcome = "Final approved"

    state.trace.append({
        "step": "verify",
        "agent": "verifier",
        "action": "Enforced grounding: evidence must exist AND final answer must show citations",
        "outcome": outcome,
    })

    return state

