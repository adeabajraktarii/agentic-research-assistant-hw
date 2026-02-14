from __future__ import annotations

from openai import OpenAI

from shared_state import SharedState

from writer.deterministic_compare import build_compare_markdown
from writer.deterministic_deadlines import build_deadlines_markdown
from writer.deterministic_top5_strict_risks import build_top5_strict_risks_markdown


def _has_citations(notes: list[dict]) -> bool:
    for n in notes or []:
        if isinstance(n, dict) and n.get("citations"):
            return True
    return False


def _build_context(notes: list[dict]) -> str:
    """
    Evidence block for the LLM.

    IMPORTANT:
    - Do NOT number items like [1], [2] because the model will mirror that in its citations.
    - We include each claim plus its first citation (source_id + location).
    """
    parts: list[str] = []

    for n in notes or []:
        if not isinstance(n, dict):
            continue

        claim = (n.get("claim") or "").strip()
        citations = n.get("citations") or []
        if not claim or not citations:
            continue

        c0 = citations[0] if isinstance(citations[0], dict) else {}
        source_id = c0.get("source_id", "unknown_source")
        location = c0.get("location", "unknown location")

        parts.append(f"- {claim}\n  (Source: {source_id} | {location})")

    return "\n".join(parts).strip()


def _llm_write(*, system_prompt: str, user_prompt: str) -> str:
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()


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
    # Special LLM prompt: Top risks (non-strict) (LOCKED SHAPE)
    # -------------------------
    if task_key == "top_risks_mitigations":
        evidence_block = _build_context(notes)

        system_prompt = (
            "You are a grounded risk analyst.\n"
            "HARD RULES:\n"
            "- Use ONLY the provided Evidence. Do not invent facts.\n"
            "- If something is missing, write exactly: 'Not found in sources'.\n"
            "- Do NOT use numeric citations like [1], [2].\n"
            "- Do NOT output the word 'citations' anywhere.\n"
            "- Use inline citations like (doc:risks.md#chunk_0).\n"
            "- Every Risk line AND every Mitigation line MUST end with real citations.\n"
            "- Mitigation must be exactly ONE sentence.\n"
        )

        user_prompt = (
            "Task:\n"
            "From the project docs, identify the top 5 risks or blockers mentioned. "
            "For each risk, add a 1-sentence mitigation plan. Include citations.\n\n"
            f"Evidence:\n{evidence_block}\n\n"
            "Output MUST be Markdown in this exact structure:\n"
            "## Deliverable Package\n"
            "### Executive Summary\n"
            "- 1–3 bullets summarizing the overall risk picture (each bullet ends with citations).\n\n"
            "### Top 5 Risks + Mitigations\n"
            "1) **Risk:** <name> (doc:...#chunk_N)\n"
            "   - **Mitigation:** <exactly 1 sentence> (doc:...#chunk_N)\n"
            "2) ... (up to 5)\n\n"
            "### Citations\n"
            "- list UNIQUE source_ids used (one per line)\n\n"
            "ABSOLUTE RULES:\n"
            "- Never write '(citations)' or the word 'citations'.\n"
            "- Every Risk line must end with real citations.\n"
            "- Every Mitigation line must end with real citations.\n"
            "- If you cannot support a risk, write:\n"
            "  **Risk:** Not found in sources\n"
            "  - **Mitigation:** Not found in sources\n"
        )

        state.draft = _llm_write(system_prompt=system_prompt, user_prompt=user_prompt)

        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "LLM grounded generation (top risks template locked)",
            "outcome": "Produced top 5 risks + 1-sentence mitigations with inline citations",
        })
        return state

    # -------------------------
    # Special LLM prompt: Confluence page (LOCKED SHAPE)
    # -------------------------
    if task_key == "draft_confluence_page":
        evidence_block = _build_context(notes)

        system_prompt = (
            "You are a grounded technical program manager writing an INTERNAL Confluence page.\n"
            "HARD RULES:\n"
            "- Use ONLY the provided Evidence. Do not invent facts.\n"
            "- If something is missing, write exactly: 'Not found in sources'.\n"
            "- Every bullet MUST end with at least one citation like (doc:...#chunk_N).\n"
            "- Use the exact section headings requested.\n"
        )

        user_prompt = (
            f"Task:\n{state.task}\n\n"
            f"Evidence:\n{evidence_block}\n\n"
            "Write a Confluence-style page in Markdown with EXACTLY these sections in this order:\n"
            "1) ## Goals\n"
            "2) ## What’s Done\n"
            "3) ## Open Risks\n"
            "4) ## Next Steps\n"
            "5) ## Key Decisions\n\n"
            "Formatting rules:\n"
            "- Each section must have 3–7 bullets.\n"
            "- EACH bullet must end with citations in parentheses, e.g. (doc:weekly_report_week13.md#chunk_0).\n"
            "- If a section has no evidence, put 1 bullet: 'Not found in sources.' (no citation required).\n"
            "- At the end, include:\n"
            "  ## Citations\n"
            "  - list unique source_ids used (one per line)\n"
        )

        state.draft = _llm_write(system_prompt=system_prompt, user_prompt=user_prompt)

        state.trace.append({
            "step": "draft",
            "agent": "writer",
            "action": "LLM grounded generation (Confluence template locked)",
            "outcome": "Confluence page drafted using evidence with per-bullet citations",
        })
        return state

    # -------------------------
    # Default LLM writer (for remaining tasks)
    # -------------------------
    evidence_block = _build_context(notes)

    system_prompt = (
        "You are a grounded business analyst.\n"
        "You MUST use ONLY the provided evidence.\n"
        "If evidence is missing, write: 'Not found in sources'.\n"
        "Do NOT invent facts.\n"
        "Every claim must be supported by the evidence.\n"
        "Use inline citations like (doc:...#chunk_N). Do NOT use [1] style citations.\n"
    )

    user_prompt = (
        f"Task:\n{state.task}\n\n"
        f"Evidence:\n{evidence_block}\n\n"
        "Produce a structured deliverable package with:\n"
        "- Executive Summary\n"
        "- Main Sections relevant to the task\n"
        "- Citations section listing all source_ids used\n"
    )

    state.draft = _llm_write(system_prompt=system_prompt, user_prompt=user_prompt)

    state.trace.append({
        "step": "draft",
        "agent": "writer",
        "action": "LLM grounded generation",
        "outcome": "Draft created using evidence",
    })
    return state






