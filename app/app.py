from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestration.graph import run_task  # noqa: E402


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    task_key: str
    prompt: str
    must_include: List[str]
    must_not_include: List[str]


def _load_eval_cases(jsonl_path: Path) -> List[EvalCase]:
    cases: List[EvalCase] = []
    if not jsonl_path.exists():
        return cases

    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)

        cases.append(
            EvalCase(
                case_id=obj.get("id", "EVAL-???"),
                task_key=obj.get("task_key", "default"),
                prompt=obj.get("prompt", ""),
                must_include=obj.get("must_include", []) or [],
                must_not_include=obj.get("must_not_include", []) or [],
            )
        )
    return cases


def _pretty_trace(trace: Any) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for item in (trace or []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "Step": item.get("step", ""),
                "Agent": item.get("agent", ""),
                "Action": item.get("action", ""),
                "Outcome": item.get("outcome", ""),
            }
        )
    return pd.DataFrame(rows)


def _extract_citations_from_text(text: str) -> List[str]:
    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines()]
    out: List[str] = []
    in_citations = False
    for ln in lines:
        if ln.lower().startswith("## citations") or ln.lower().startswith("### citations"):
            in_citations = True
            continue
        if in_citations:
            if ln.startswith("## "):
                break
            if ln.startswith("-"):
                out.append(ln.lstrip("-").strip())
    seen = set()
    uniq = []
    for c in out:
        if c and c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def _init_run_history():
    if "run_history" not in st.session_state:
        st.session_state.run_history = []  


def _log_run(
    *,
    kind: str,
    task_key: str,
    prompt_preview: str,
    result: dict,
    elapsed_ms: int,
    eval_pass: Optional[bool] = None,
):
    trace = (result or {}).get("trace", []) or []
    draft = (result or {}).get("draft", "") or ""

    # basic signals (safe + stable)
    retrieved_chunks = 0
    for t in trace:
        if isinstance(t, dict) and t.get("step") == "research":
            
            outcome = str(t.get("outcome", ""))
            for token in outcome.split():
                if token.isdigit():
                    retrieved_chunks = int(token)
                    break

    citations = _extract_citations_from_text(draft)
    status = "ok" if draft.strip() else "empty"

    if kind == "eval" and eval_pass is not None:
        status = "pass" if eval_pass else "fail"

    st.session_state.run_history.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kind": kind,  # task/eval
            "task_key": task_key,
            "latency_ms": elapsed_ms,
            "chunks": retrieved_chunks,
            "citations": len(citations),
            "status": status,
            "prompt_preview": prompt_preview[:80].replace("\n", " ").strip(),
        },
    )


def _render_run_history():
    _init_run_history()
    st.sidebar.markdown("### Run History")
    if not st.session_state.run_history:
        st.sidebar.caption("No runs yet.")
        return

    df = pd.DataFrame(st.session_state.run_history)
    st.sidebar.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "time": st.column_config.TextColumn("Time", width="small"),
            "kind": st.column_config.TextColumn("Kind", width="small"),
            "task_key": st.column_config.TextColumn("Task", width="small"),
            "latency_ms": st.column_config.NumberColumn("ms", width="small"),
            "chunks": st.column_config.NumberColumn("Chunks", width="small"),
            "citations": st.column_config.NumberColumn("Cites", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "prompt_preview": st.column_config.TextColumn("Prompt", width="large"),
        },
    )

    col_a, col_b = st.sidebar.columns(2)
    with col_a:
        if st.button("Clear history"):
            st.session_state.run_history = []
            st.rerun()
    with col_b:
        st.caption("")

def _score_eval_case(case: EvalCase, draft: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Simple, stable scoring:
    - all must_include substrings must appear (case-insensitive)
    - all must_not_include substrings must NOT appear (case-insensitive)
    """
    text = (draft or "").lower()

    missing = []
    for s in case.must_include or []:
        if (s or "").strip() and (s.lower() not in text):
            missing.append(s)

    forbidden_found = []
    for s in case.must_not_include or []:
        if (s or "").strip() and (s.lower() in text):
            forbidden_found.append(s)

    passed = (len(missing) == 0) and (len(forbidden_found) == 0)

    details = {
        "missing": missing,
        "forbidden_found": forbidden_found,
    }
    return passed, details


st.set_page_config(page_title="Agentic Research Assistant", layout="wide")
st.title("Agentic Research & Action Assistant")

mode = st.sidebar.radio("Mode", ["Run Task", "Run Eval"], index=0)
_render_run_history()

TASK_PRESETS: List[Tuple[str, str]] = [
    ("compare_approaches", "Compare two approaches described in docs and recommend one with justification."),
    ("extract_deadlines_and_owners", "Extract all deadlines + owners from docs and format them into an action list."),
    ("top5_risks_mitigations_strict", "Summarize the top 5 risks mentioned across these project docs and propose mitigations."),
    ("top_risks_mitigations", "Summarize the top 5 risks mentioned across these project docs and propose mitigations."),
    ("client_update_email", "Create a client update email from the latest weekly report doc."),
    ("draft_confluence_page", "Draft an internal Confluence page from a set of markdown notes."),
    ("default", "Ask a grounded question using the project docs."),
]

TASK_KEYS = [k for (k, _) in TASK_PRESETS]
TASK_DEFAULT_PROMPT = {k: p for (k, p) in TASK_PRESETS}

if "task_key" not in st.session_state:
    st.session_state.task_key = "compare_approaches"
if "task_text" not in st.session_state:
    st.session_state.task_text = TASK_DEFAULT_PROMPT[st.session_state.task_key]


def _on_task_key_change():
    k = st.session_state.task_key
    st.session_state.task_text = TASK_DEFAULT_PROMPT.get(k, "")


if mode == "Run Task":
    st.subheader("Run Task")

    st.selectbox(
        "Task key",
        TASK_KEYS,
        key="task_key",
        on_change=_on_task_key_change,
        help="Selecting a task auto-fills the question box (you can still edit it).",
    )

    task_text = st.text_area("Task", key="task_text", height=160)
    run = st.button("Run task", type="primary")

    if run:
        t0 = time.perf_counter()
        with st.spinner("Running multi-agent workflow..."):
            result = run_task(task_text, task_key=st.session_state.task_key)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        _init_run_history()
        _log_run(
            kind="task",
            task_key=st.session_state.task_key,
            prompt_preview=task_text,
            result=result or {},
            elapsed_ms=elapsed_ms,
        )

        draft = (result or {}).get("draft", "") or ""
        trace = (result or {}).get("trace", []) or []

        st.markdown("## Answer")
        st.markdown(draft if draft else "_No output_")

        st.markdown("## Trace Log")
        df = _pretty_trace(trace)
        if len(df) == 0:
            st.write("_No trace available_")
        else:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Step": st.column_config.TextColumn(width="small"),
                    "Agent": st.column_config.TextColumn(width="small"),
                    "Action": st.column_config.TextColumn(width="large"),
                    "Outcome": st.column_config.TextColumn(width="large"),
                },
            )


else:
    st.subheader("Run Eval")

    eval_path = ROOT / "eval" / "questions.jsonl"
    cases = _load_eval_cases(eval_path)

    if not cases:
        st.error(f"No eval cases found at: {eval_path}")
        st.stop()

    labels = [f"{c.case_id}  •  {c.task_key}" for c in cases]
    idx = st.selectbox("Eval case", list(range(len(cases))), format_func=lambda i: labels[i])
    case = cases[idx]

    with st.expander("Case details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Case ID:** {case.case_id}")
            st.write(f"**Task key:** `{case.task_key}`")
        with col2:
            st.write(f"**Must include:** {len(case.must_include)} check(s)")
            st.write(f"**Must NOT include:** {len(case.must_not_include)} check(s)")

    prompt = st.text_area("Eval question (editable for this run)", value=case.prompt, height=160)
    run_eval = st.button("Run eval case", type="primary")

    if run_eval:
        t0 = time.perf_counter()
        with st.spinner("Running eval case..."):
            result = run_task(prompt, task_key=case.task_key)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        draft = (result or {}).get("draft", "") or ""
        trace = (result or {}).get("trace", []) or []

        passed, details = _score_eval_case(case, draft)

        _init_run_history()
        _log_run(
            kind="eval",
            task_key=case.task_key,
            prompt_preview=prompt,
            result=result or {},
            elapsed_ms=elapsed_ms,
            eval_pass=passed,
        )

        
        if passed:
            st.success(f"✅ PASS — {case.case_id}")
        else:
            st.error(f"❌ FAIL — {case.case_id}")

        
        if not passed:
            with st.expander("Why it failed", expanded=True):
                if details.get("missing"):
                    st.markdown("**Missing required phrases:**")
                    for s in details["missing"]:
                        st.write(f"- {s}")
                if details.get("forbidden_found"):
                    st.markdown("**Contains forbidden phrases:**")
                    for s in details["forbidden_found"]:
                        st.write(f"- {s}")

        st.markdown("## Answer")
        st.markdown(draft if draft else "_No output_")

        st.markdown("## Trace Log")
        df = _pretty_trace(trace)
        if len(df) == 0:
            st.write("_No trace available_")
        else:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Step": st.column_config.TextColumn(width="small"),
                    "Agent": st.column_config.TextColumn(width="small"),
                    "Action": st.column_config.TextColumn(width="large"),
                    "Outcome": st.column_config.TextColumn(width="large"),
                },
            )
