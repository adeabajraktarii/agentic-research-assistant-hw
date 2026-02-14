from __future__ import annotations

from openai import OpenAI

from shared_state import SharedState

from writer.deterministic_compare import build_compare_markdown
from writer.deterministic_deadlines import build_deadlines_markdown
from writer.deterministic_top5_strict_risks import build_top5_strict_risks_markdown


def _has_citations(notes: list[dict]) -> bool:
    for n in notes or []:
        cits = n.get("citations")
        if isinstance(cits, list) and len(cits) > 0:
            return True
    return False


def _note_text(n: dict) -> str:
    """Pull evidence text from any common key shape."""
    if not isinstance(n, dict):
        return ""

    for k in ("claim", "content", "text", "page_content", "snippet", "chunk_text", "passage"):
        v = n.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # fallback: sometimes only quotes exist
    cits = n.get("citations") or []
    if isinstance(cits, list):
        parts: list[str] = []
        for c in cits:
            if not isinstance(c, dict):
                continue
            for k in ("quote", "text", "excerpt"):
                v = c.get(k)
                if isinstance(v, str) and v.strip():
                    parts.append(v.strip())
        if parts:
            return "\n".join(parts)

    return ""


def _build_context(notes: list[dict]) -> str:
    """
    Build evidence block for the LLM writer.
    Includes short evidence snippets + source_id + location.
    """
    parts: list[str] = []

    for i, n in enumerate(notes or []):
        evidence = _note_text(n)
        citations = n.get("citations") or []

        if not isinstance(citations, list) or not citations:
            continue
        if not evidence:
            continue

        first = citations[0] if isinstance(citations[0], dict) else {}
        source_id = first.get("source_id", "unknown_source")
        location = first.get("location", first.get("locator", "unknown location"))

        parts.append(f"[{i+1}] {evidence}\n(Source: {source_id} | {location})")

    return "\n\n".join(parts)


def writer_agent(state: SharedState) -> SharedState:
    notes = state.research_notes or []
    task_key = (state.task_key or "").strip()

    # If no citations, hard-stop safely
    if not _has_citations(notes):
        state.draft = (
            "## Deliverable Package\n\n"
            "### Executive Summary\n"
            "- Not found in the sources.\n"
        )
        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "Draft generation",
            "outcome": "No citations available",
        })
        return state

    # -------------------------
    # Deterministic tasks (locked)
    # -------------------------
    if task_key == "compare_approaches":
        state.draft = build_compare_markdown(notes)
        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "Deterministic comparison (Option A vs Option B)",
            "outcome": "Produced 2–4 bullets per option + exactly 3 grounded reasons",
        })
        return state

    if task_key == "extract_deadlines_and_owners":
        state.draft = build_deadlines_markdown(notes)
        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "Deterministic extraction (deadlines + owners)",
            "outcome": "Extracted rows only from explicit evidence (no invented items)",
        })
        return state

    if task_key == "top5_risks_mitigations_strict":
        state.draft = build_top5_strict_risks_markdown(notes)
        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "Deterministic extraction (top5 strict risks)",
            "outcome": "Extracted risks from evidence (+optional pricing support when found)",
        })
        return state

    # -------------------------
    # LLM writer for the rest
    # -------------------------
    evidence_block = _build_context(notes)

    if not evidence_block.strip():
        state.draft = (
            "## Deliverable Package\n\n"
            "### Executive Summary\n"
            "- Not found in the sources.\n"
        )
        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "Draft generation",
            "outcome": "Evidence block empty after filtering",
        })
        return state

    system_prompt = (
        "You are a grounded business analyst.\n"
        "You MUST use ONLY the provided evidence.\n"
        "If evidence is missing, write: 'Not found in sources'.\n"
        "Do NOT invent facts.\n"
        "Every claim must be supported by the evidence.\n"
    )

    user_prompt = (
        f"Task:\n{state.task}\n\n"
        f"Evidence:\n{evidence_block}\n\n"
        "Output rules:\n"
        "- Use clear headings\n"
        "- Keep it concise and client-ready\n"
        "- Include inline citations like (doc:file.md#chunk_0)\n"
        "- End with a Citations list of the source_ids you used\n"
    )

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    state.draft = response.choices[0].message.content

    state.trace.append({
        "step": "draft",
        "agent": "writer",
        "action": "LLM grounded generation",
        "outcome": "Draft created using evidence",
    })
    return state



