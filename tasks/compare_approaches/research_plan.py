from __future__ import annotations

from pathlib import Path
from typing import Any

from shared_state import SharedState
from retrieval.retriever import search_docs
from retrieval.research_utils import dedupe_results_keep_order

DOCS_DIR = Path("data") / "docs"


def retrieve_compare(query: str) -> list[dict]:
    results = search_docs(query, top_k=8, must_include="technical_decisions.md", overfetch=40)

    forced = search_docs(
        "Current Recommendation Week 12 Option A In-House contingency Week 16 technical_decisions.md",
        top_k=3,
        must_include="technical_decisions.md",
        overfetch=20,
    )

    return dedupe_results_keep_order(results + forced)[:12]


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="ignore")
    except Exception:
        return ""


def _extract_between(text: str, start_marker: str, end_marker: str) -> str:
    if not text:
        return ""
    start_idx = text.find(start_marker)
    if start_idx == -1:
        return ""
    start_idx += len(start_marker)
    end_idx = text.find(end_marker, start_idx)
    if end_idx == -1:
        return ""
    return text[start_idx:end_idx].strip()


def postprocess_compare(state: SharedState) -> None:
    """
    Deterministic injection:
    Read data/docs/technical_decisions.md and extract the Option A/Option B section
    so the writer always has both options even if chunking changes.
    """
    td_path = DOCS_DIR / "technical_decisions.md"
    raw = _read_text_file(td_path)
    if not raw.strip():
        return

    options_block = _extract_between(raw, start_marker="### Option A:", end_marker="## Current Recommendation")
    if not options_block:
        return

    injected_text = "### Option A:\n" + options_block

    citation = {
        "source_id": "doc:technical_decisions.md#anchor_options",
        "quote": injected_text.replace("\n", " ")[:260] + ("..." if len(injected_text) > 260 else ""),
        "location": "anchor — Option A/Option B section (between '### Option A:' and '## Current Recommendation')",
    }

    injected_note = {"claim": injected_text, "citations": [citation]}

    # put first
    state.research_notes = [injected_note] + (state.research_notes or [])
