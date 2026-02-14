from __future__ import annotations

from typing import Any, Dict, List


def dedupe_results_keep_order(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Dedupe retrieval results while preserving order.
    Uses source_id if present, otherwise uses content prefix.
    """
    merged: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for r in results or []:
        sid = (r.get("source_id") or "").strip()
        content = (r.get("content") or "").strip()
        key = sid or content[:80]
        key = (key or "").strip()

        if not key or key in seen:
            continue

        seen.add(key)
        merged.append(r)

    return merged
