from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

# Allow running from /eval even when executed directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from orchestration.graph import run_task  # noqa: E402


@dataclass
class EvalCase:
    id: str
    task_key: str
    task_text: str
    must_contain: List[str]
    must_not_contain: List[str]


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _to_case(d: Dict[str, Any]) -> EvalCase:
    return EvalCase(
        id=str(d["id"]),
        task_key=str(d["task_key"]),
        task_text=str(d["task_text"]),
        must_contain=list(d.get("must_contain", [])),
        must_not_contain=list(d.get("must_not_contain", [])),
    )


def _get_output_text(result: Dict[str, Any]) -> str:
    # Your pipeline uses state.final_output in some versions, and state.draft in others.
    # Prefer final_output if present, else draft, else stringify.
    if isinstance(result, dict):
        for key in ("final_output", "draft", "output", "result"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return val
    return json.dumps(result, ensure_ascii=False, indent=2)


def _contains(text: str, needle: str) -> bool:
    """
    If needle looks like a regex (contains \\ or special char), we still treat as plain substring
    EXCEPT we allow users to embed escaped sequences like \\n in jsonl; normalize those.
    """
    needle_norm = needle.encode("utf-8").decode("unicode_escape")
    return needle_norm in text


def run_case(case: EvalCase) -> Tuple[bool, List[str]]:
    result = run_task(case.task_text, task_key=case.task_key)
    out = _get_output_text(result)

    failures: List[str] = []

    for s in case.must_contain:
        if not _contains(out, s):
            failures.append(f"Missing required text: {s}")

    for s in case.must_not_contain:
        if _contains(out, s):
            failures.append(f"Found forbidden text: {s}")

    return (len(failures) == 0), failures


def main() -> None:
    questions_path = os.path.join(os.path.dirname(__file__), "questions.jsonl")
    rows = _read_jsonl(questions_path)
    cases = [_to_case(r) for r in rows]

    passed = 0
    failed = 0

    print(f"Loaded {len(cases)} eval cases from {questions_path}\n")

    for c in cases:
        ok, failures = run_case(c)
        if ok:
            passed += 1
            print(f"✅ {c.id} ({c.task_key})")
        else:
            failed += 1
            print(f"❌ {c.id} ({c.task_key})")
            for f in failures:
                print(f"   - {f}")
        print()

    total = passed + failed
    print("========== SUMMARY ==========")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    # Non-zero exit code if anything failed (useful for CI)
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
