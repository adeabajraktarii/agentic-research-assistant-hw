from __future__ import annotations

from typing import List, Dict, Optional


def _first_source_id(note: dict) -> Optional[str]:
    cits = note.get("citations") or []
    if isinstance(cits, list) and cits:
        sid = cits[0].get("source_id")
        if isinstance(sid, str) and sid.strip():
            return sid.strip()
    return None


def _parse_action_items_table_from_action_items_md(notes: List[dict]) -> List[Dict[str, str]]:
    """
    Deterministic extraction for extract_deadlines_and_owners.

    RULE: Only include rows that *explicitly* contain:
      Priority | Item | Owner | Due Date | Status
    and come from action_items.md evidence.

    We purposely DO NOT invent rows from roadmap/weekly reports here,
    because your requirement is: only include action items with Owner + Due Date.
    """
    rows: List[Dict[str, str]] = []

    # Find the action_items chunk(s)
    for n in notes or []:
        sid = (_first_source_id(n) or "").lower()
        if "doc:action_items.md" not in sid:
            continue

        text = (n.get("claim") or "").strip()
        if not text:
            continue

        # Parse markdown table rows
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        table_lines = [ln for ln in lines if ln.startswith("|") and ln.endswith("|")]

        if len(table_lines) < 3:
            continue

        # First is header, second is separator, rest are rows
        data_lines = table_lines[2:]

        for ln in data_lines:
            cols = [c.strip() for c in ln.strip("|").split("|")]
            if len(cols) < 5:
                continue

            priority, item, owner, due_date, status = cols[:5]

            # Hard requirement: Owner and Due Date must be present
            if not owner or not due_date:
                continue

            rows.append({
                "priority": priority,
                "item": item,
                "owner": owner,
                "due_date": due_date,
                "status": status,
                "cite": _first_source_id(n) or "doc:action_items.md",
            })

    # Deduplicate by (priority,item,owner,due_date)
    seen = set()
    out: List[Dict[str, str]] = []
    for r in rows:
        key = (r["priority"], r["item"], r["owner"], r["due_date"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)

    return out


def build_deadlines_markdown(notes: List[dict]) -> str:
    rows = _parse_action_items_table_from_action_items_md(notes)

    if not rows:
        return (
            "## Deliverable Package\n\n"
            "### Executive Summary\n"
            "- Not found in sources.\n"
        )

    cite = rows[0]["cite"]

    lines: List[str] = []
    lines.append("## Deliverable Package\n")
    lines.append("### Executive Summary")
    lines.append("- Action items extracted that explicitly include Owner and Due Date.\n")
    lines.append("### Action Items")
    lines.append("| Priority | Item | Owner | Due Date | Status |")
    lines.append("|---|---|---|---|---|")

    for r in rows:
        lines.append(
            f"| {r['priority']} | {r['item']} | {r['owner']} | {r['due_date']} | {r['status']} ({r['cite']}) |"
        )

    lines.append("\n### Citations")
    lines.append(f"- {cite}")

    return "\n".join(lines).strip()
