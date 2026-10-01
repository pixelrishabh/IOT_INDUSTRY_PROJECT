"""
ingest.py - Ingest and Index Oil & Gas Domain Knowledge Documents into Vector Store
Reads markdown documents from rag/documents/, splits them by sections,
and builds the persistent vector store index.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List

from rag.vector_store import KnowledgeVectorStore


def extract_event_id(filename: str) -> int:
    """Extract event id integer from filename like event_1_abrupt_increase_bsw.md"""
    match = re.search(r"event_(\d+)", filename)
    if match:
        return int(match.group(1))
    return -1


def parse_markdown_document(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a markdown document into semantic sections for retrieval."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    event_id = extract_event_id(file_path.name)
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else file_path.stem

    # Split document by markdown level 2 headers (##)
    sections = re.split(r"\n(?=##\s+)", content)
    chunks = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.search(r"^##\s+(.+)$", sec, re.MULTILINE)
        section_title = header_match.group(1).strip() if header_match else "Overview"

        chunk_id = f"{file_path.stem}_{len(chunks)+1}"
        full_text = f"Document: {doc_title}\nSection: {section_title}\nEvent ID: {event_id}\n\n{sec}"

        chunks.append({
            "chunk_id": chunk_id,
            "doc_name": file_path.name,
            "doc_title": doc_title,
            "section_title": section_title,
            "event_id": event_id,
            "content": full_text
        })

    return chunks


def ingest_all_documents(docs_dir: str = "rag/documents", store_dir: str = "rag/vector_store"):
    print("==================================================")
    print("PHASE 6: RAG KNOWLEDGE BASE INGESTION")
    print("==================================================")

    docs_path = Path(docs_dir)
    doc_files = sorted(list(docs_path.glob("*.md")))

    if not doc_files:
        raise FileNotFoundError(f"No markdown documents found in {docs_dir}!")

    print(f"Found {len(doc_files)} technical knowledge documents:")
    all_chunks = []
    for f in doc_files:
        chunks = parse_markdown_document(f)
        all_chunks.extend(chunks)
        print(f"  - {f.name:35s} -> {len(chunks)} chunks")

    print(f"\nTotal extracted knowledge chunks: {len(all_chunks)}")

    store = KnowledgeVectorStore(store_dir=store_dir)
    store.build_store(all_chunks)
    print(f"Vector store successfully saved to: {store_dir}")


if __name__ == "__main__":
    ingest_all_documents()
