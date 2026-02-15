from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


RISK_ID_RE = re.compile(r"\b(R-\d{3})\s*:\s*([^\n\r]+)")
SEVERITY_RE = re.compile(r"(?:Severity|SEVERITY)\s*[:\-]\s*(.+)", re.IGNORECASE)
IMPACT_RE = re.compile(r"(?:Impact|IMPACT)\s*[:\-]\s*(.+)", re.IGNORECASE)
MITIGATION_RE = re.compile(r"(?:Mitigation|MITIGATION)\s*[:\-]\s*(.+)", re.IGNORECASE)


MD_FIELD_RE = {
    "severity": re.compile(r"\*\*Severity\*\*\s*[:\-]\s*(.+)", re.IGNORECASE),
    "impact": re.compile(r"\*\*Impact\*\*\s*[:\-]\s*(.+)", re.IGNORECASE),
    "mitigation": re.compile(r"\*\*Mitigation\*\*\s*[:\-]\s*(.+)", re.IGNORECASE),
}


def _clean(s: Optional[str]) -> str:
    if not s:
        return ""

    s = s.strip()
    s = re.sub(r"^\s*[-•]\s*", "", s)
    s = s.replace("**", "").strip()
    return s


def _pick_source_id(note: dict) -> str:
    cits = note.get("citations") or []
    if isinstance(cits, list) and cits and isinstance(cits[0], dict):
        return cits[0].get("source_id", "") or ""
    return ""


def _pick_text(note: dict) -> str:
    for k in ("claim", "content", "text", "page_content", "snippet", "chunk_text", "passage"):
        v = note.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _is_risks_doc(source_id: str) -> bool:
    return "risks.md" in (source_id or "").lower()


def _is_pricing_doc(source_id: str) -> bool:
    return "pricing_and_packaging.md" in (source_id or "").lower()


def _extract_fields_from_window(window_text: str) -> Tuple[str, str, str]:
    """
    Try multiple patterns for Severity / Impact / Mitigation inside a small window of text.
    """
    severity = ""
    impact = ""
    mitigation = ""

    m = SEVERITY_RE.search(window_text)
    if m:
        severity = _clean(m.group(1))

    m = IMPACT_RE.search(window_text)
    if m:
        impact = _clean(m.group(1))

    m = MITIGATION_RE.search(window_text)
    if m:
        mitigation = _clean(m.group(1))

    if not severity:
        m = MD_FIELD_RE["severity"].search(window_text)
        if m:
            severity = _clean(m.group(1))

    if not impact:
        m = MD_FIELD_RE["impact"].search(window_text)
        if m:
            impact = _clean(m.group(1))

    if not mitigation:
        m = MD_FIELD_RE["mitigation"].search(window_text)
        if m:
            mitigation = _clean(m.group(1))

    return severity, impact, mitigation


def _risk_order_key(risk_id: str) -> int:
    m = re.search(r"R-(\d{3})", risk_id)
    return int(m.group(1)) if m else 9999


def build_top5_strict_risks_markdown(notes: List[dict]) -> str:
    """
    Deterministic strict risk builder.

    Rules:
    - Titles MUST come only from lines like: R-001: Something
    - Prefer risks.md citations for each risk
    - Optional: add pricing_and_packaging.md as secondary support for R-004 only
    """
    notes = notes or []

    risks_notes = [n for n in notes if _is_risks_doc(_pick_source_id(n))]
    pricing_notes = [n for n in notes if _is_pricing_doc(_pick_source_id(n))]

    if not risks_notes:
        return (
            "## Deliverable Package: Top 5 Risks\n\n"
            "### Executive Summary\n"
            "- Not found in sources.\n\n"
            "### Top 5 Risks\n"
            "- Not found in sources.\n\n"
            "## Citations\n"
            "- Not found in sources\n"
        )

    extracted: Dict[str, Dict[str, str]] = {}
    risk_citations: Dict[str, List[str]] = {}

    for n in risks_notes:
        source_id = _pick_source_id(n)
        text = _pick_text(n)
        if not text:
            continue

        for match in RISK_ID_RE.finditer(text):
            rid = match.group(1).strip()
            title = _clean(match.group(2))

            start = match.start()
            window = text[start : start + 600]

            severity, impact, mitigation = _extract_fields_from_window(window)

            if rid not in extracted:
                extracted[rid] = {
                    "title": title,
                    "severity": severity or "Not found in sources",
                    "impact": impact or "Not found in sources",
                    "mitigation": mitigation or "Not found in sources",
                }
                risk_citations[rid] = [source_id] if source_id else []
            else:
                if extracted[rid].get("title") in ("", "Not found in sources") and title:
                    extracted[rid]["title"] = title
                if extracted[rid]["severity"] == "Not found in sources" and severity:
                    extracted[rid]["severity"] = severity
                if extracted[rid]["impact"] == "Not found in sources" and impact:
                    extracted[rid]["impact"] = impact
                if extracted[rid]["mitigation"] == "Not found in sources" and mitigation:
                    extracted[rid]["mitigation"] = mitigation

                if source_id and source_id not in risk_citations[rid]:
                    risk_citations[rid].append(source_id)
                    
    risk_ids = sorted(extracted.keys(), key=_risk_order_key)[:5]

    if "R-004" in risk_ids and pricing_notes:
        pricing_source_ids = []
        for n in pricing_notes:
            sid = _pick_source_id(n)
            txt = _pick_text(n).lower()
            if any(k in txt for k in ["pricing", "discount", "churn", "sensitivity"]):
                if sid:
                    pricing_source_ids.append(sid)

        if pricing_source_ids:
            sid = pricing_source_ids[0]
            if sid not in risk_citations.get("R-004", []):
                risk_citations.setdefault("R-004", []).append(sid)

    lines: List[str] = []
    lines.append("# Deliverable Package: Top 5 Risks\n")
    lines.append("## Executive Summary")
    lines.append("This document outlines the top five risks identified in the project documents, including severity, impact, mitigation, and citations.\n")
    lines.append("## Top 5 Risks\n")

    all_citations: List[str] = []

    for i, rid in enumerate(risk_ids, start=1):
        r = extracted[rid]
        title = r.get("title") or "Not found in sources"
        severity = r.get("severity") or "Not found in sources"
        impact = r.get("impact") or "Not found in sources"
        mitigation = r.get("mitigation") or "Not found in sources"
        cits = risk_citations.get(rid, [])
        cits = [c for c in cits if c]  

        if not cits:
            cits = [_pick_source_id(risks_notes[0])]

        for c in cits:
            if c not in all_citations:
                all_citations.append(c)

        lines.append(f"### {i}. {rid}: {title}")
        lines.append(f"- **Severity:** {severity}")
        lines.append(f"- **Impact:** {impact}")
        lines.append(f"- **Mitigation:** {mitigation}")
        lines.append(f"- **Citation:** ({'; '.join(cits)})\n")

    lines.append("## Citations")
    for c in all_citations:
        lines.append(f"- ({c})")

    lines.append("")  
    return "\n".join(lines)
