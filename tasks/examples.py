from __future__ import annotations

EXAMPLE_TASKS = {
    "client_update_email": {
        "description": "Draft a client-ready weekly update email.",
        "task": (
            "Summarize competitor positioning from our docs and draft a client-ready "
            "weekly update email with Progress, Risks, and Next steps. Use citations."
        ),
        "expected_artifact_type": "client_update_email",
    },
    "top_risks_mitigations": {
        "description": "Identify top risks with mitigations.",
        "task": (
            "From the project docs, identify the top 5 risks or blockers mentioned. "
            "For each risk, add a 1-sentence mitigation plan. Include citations."
        ),
        "expected_artifact_type": "top_risks",
    },
    "top5_risks_mitigations_strict": {
        "description": "Strict risk extraction with structured fields.",
        "task": (
            "Identify the top 5 risks across project documents and list each with "
            "severity, impact, mitigation, and citation."
        ),
        "expected_artifact_type": "strict_risks",
    },
    "compare_approaches": {
        "description": "Compare approaches and recommend one.",
        "task": (
            "Compare Option A vs Option B using ONLY the project docs. "
            "Your artifact MUST include these sections:\n"
            "1) Option A: 2–4 bullets (pros/cons or key points)\n"
            "2) Option B: 2–4 bullets (pros/cons or key points)\n"
            "3) Recommendation: pick ONE option and give exactly 3 reasons.\n"
            "Rules:\n"
            "- Every bullet and every reason MUST be directly supported by evidence.\n"
            "- Do NOT invent Option B if it isn’t described; instead write: 'Not stated in sources'.\n"
            "- Each reason must include citations.\n"
        ),
        "expected_artifact_type": "comparison",
    },
    "extract_deadlines_and_owners": {
        "description": "Extract action items with owner and due date.",
        "task": (
            "Extract all action items that include an Owner and Due Date, "
            "and output them as a bullet list or table with: "
            "Priority | Item | Owner | Due Date | Status. "
            "Use only evidence from docs; if a field is missing, say "
            "'Not found in sources'."
        ),
        "expected_artifact_type": "action_list",
    },
    "draft_confluence_page": {
        "description": "Draft an internal Confluence-style summary page.",
        "task": (
            "Draft an internal Confluence-style page summarizing: Goals, "
            "What’s Done, Open Risks, Next Steps, and Key Decisions. "
            "Use only evidence from docs and cite each section."
        ),
        "expected_artifact_type": "confluence_page",
    },
}
