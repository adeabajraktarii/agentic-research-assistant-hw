from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from openai import OpenAI

from retrieval.index_store import INDEX_DIR

_CACHED_INDEX: Optional[faiss.Index] = None
_CACHED_META: Optional[List[Dict[str, Any]]] = None

FAISS_INDEX_PATH = INDEX_DIR / "faiss_index" / "index.faiss"
META_PATH = INDEX_DIR / "chunks_meta.jsonl"


def _load_meta() -> List[Dict[str, Any]]:
    if not META_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {META_PATH}")
    rows: List[Dict[str, Any]] = []
    with META_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_index() -> faiss.Index:
    if not FAISS_INDEX_PATH.exists():
        raise FileNotFoundError(f"Missing FAISS index file: {FAISS_INDEX_PATH}")
    return faiss.read_index(str(FAISS_INDEX_PATH))


def _get_index_and_meta() -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    global _CACHED_INDEX, _CACHED_META
    if _CACHED_INDEX is None or _CACHED_META is None:
        _CACHED_INDEX = _load_index()
        _CACHED_META = _load_meta()
    return _CACHED_INDEX, _CACHED_META


def _embed_query(text: str) -> List[float]:
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    client = OpenAI()
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding


def _row_to_result(row: Dict[str, Any], score: float) -> Dict[str, Any]:
    """
    Our meta rows come from index_store.py:
      {"page_content": "...", "metadata": {...}}
    """
    md = row.get("metadata") or {}
    return {
        "content": (row.get("page_content") or "").strip(),
        "source_id": md.get("source_id") or "unknown_source",
        "source": md.get("source_name") or md.get("source_path") or "unknown",
        "locator": md.get("locator") or "unknown location",
        "score": float(score),
        "metadata": md,
    }


def search_docs(
    query: str,
    top_k: int = 5,
    must_include: Optional[str] = None,
    overfetch: int = 30,
) -> List[Dict[str, Any]]:
    """
    Vector search over local FAISS index.
    Returns list of dicts with: content, source_id, source, locator, score.
    If must_include is provided, we overfetch and ensure up to 2 matches are included.
    """
    index, meta = _get_index_and_meta()

    q_emb = _embed_query(query)
    xq = np.array([q_emb], dtype="float32")

    n_fetch = max(overfetch, top_k) if must_include else top_k
    distances, indices = index.search(xq, n_fetch)

    results: List[Dict[str, Any]] = []
    for dist, idx in zip(distances[0], indices[0]):
        if int(idx) == -1:
            continue
        row = meta[int(idx)]
        content = (row.get("page_content") or "").strip()
        if not content:
            continue
        results.append(_row_to_result(row, score=float(dist)))

    if must_include:
        needle = must_include.lower()
        forced = [r for r in results if needle in (r.get("source_id") or "").lower() or needle in (r.get("source") or "").lower()]

        if forced:
            forced = forced[:2] 
            seen = {r["source_id"] for r in forced if r.get("source_id")}
            for r in results:
                if len(forced) >= top_k:
                    break
                sid = r.get("source_id")
                if sid and sid in seen:
                    continue
                forced.append(r)
                if sid:
                    seen.add(sid)
            return forced[:top_k]

    return results[:top_k]
