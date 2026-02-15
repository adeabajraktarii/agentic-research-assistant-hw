from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_EXTS = {".txt", ".md"}  


def _extract_md_headings(text: str) -> List[Tuple[int, str]]:
    
    headings: List[Tuple[int, str]] = []
    for i, line in enumerate(text.splitlines()):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            heading_text = stripped.lstrip("#").strip()
            if heading_text:
                headings.append((i + 1, heading_text))
    return headings


def _extract_md_title(text: str) -> Optional[str]:
    
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None


def load_raw_documents(docs_dir: str = "data/docs") -> List[Document]:
    
    base = Path(docs_dir)
    if not base.exists():
        raise FileNotFoundError(f"Docs folder not found: {docs_dir}")

    docs: List[Document] = []
    for path in base.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue

            title = _extract_md_title(text) if path.suffix.lower() == ".md" else None

            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source_path": str(path).replace("\\", "/"),
                        "source_name": path.name,
                        "file_ext": path.suffix.lower(),
                        "source_title": title,
                        "doc_id": f"doc:{path.name}",
                    },
                )
            )

    return docs


def chunk_documents(
    docs: List[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> List[Document]:
    """
    Splits documents into chunks and attaches chunk-level metadata.
    Adds: chunk_id, source_id, line_start/line_end, section_heading, locator (for md).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )

    chunked: List[Document] = []

    for doc in docs:
        full_text = doc.page_content
        file_ext = (doc.metadata or {}).get("file_ext")
        md_headings = _extract_md_headings(full_text) if file_ext == ".md" else []
        doc_id = (doc.metadata or {}).get("doc_id") or f"doc:{(doc.metadata or {}).get('source_name')}"

        splits = splitter.split_documents([doc])

        for i, s in enumerate(splits):
            s.metadata = dict(s.metadata or {})

            s.metadata["chunk_id"] = i  
            s.metadata["source_id"] = f"{doc_id}#chunk_{i}"

            start_idx = s.metadata.get("start_index")
            if isinstance(start_idx, int):
                prefix = full_text[:start_idx]
                line_start = prefix.count("\n") + 1

                end_idx = start_idx + len(s.page_content)
                prefix_end = full_text[:end_idx]
                line_end = prefix_end.count("\n") + 1

                s.metadata["line_start"] = line_start
                s.metadata["line_end"] = line_end

                if md_headings:
                    nearest_heading_text: Optional[str] = None
                    nearest_heading_line: Optional[int] = None
                    for ln, heading in md_headings:
                        if ln <= line_start:
                            nearest_heading_line = ln
                            nearest_heading_text = heading
                        else:
                            break

                    if nearest_heading_text:
                        s.metadata["section_heading"] = nearest_heading_text
                        s.metadata["section_heading_line"] = nearest_heading_line

            chunk_id = s.metadata.get("chunk_id")
            line_start = s.metadata.get("line_start")
            line_end = s.metadata.get("line_end")
            section_heading = s.metadata.get("section_heading")

            locator_parts: List[str] = []
            if chunk_id is not None:
                locator_parts.append(f"chunk {chunk_id}")

            if file_ext == ".md" and section_heading:
                locator_parts.append(f"## {section_heading}")

            if line_start is not None and line_end is not None:
                locator_parts.append(f"lines {line_start}–{line_end}")

            if locator_parts:
                s.metadata["locator"] = " — ".join(locator_parts)

            chunked.append(s)

    return chunked


def load_and_chunk(docs_dir: str = "data/docs") -> List[Document]:
    raw = load_raw_documents(docs_dir=docs_dir)
    return chunk_documents(raw)
