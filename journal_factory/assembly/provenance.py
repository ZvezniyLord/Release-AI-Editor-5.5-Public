from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class ProvenanceEntry:
    article_id: str
    source_part: str
    source_index: int | None
    source_hash: str
    semantic_role: str
    operation: str
    final_paragraph_index: int
    final_style_id: str


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def make_paragraph_provenance(
    article_id: str,
    source_index: int | None,
    source_text: str,
    semantic_role: str,
    operation: str,
    final_paragraph_index: int,
    final_style_id: str,
) -> ProvenanceEntry:
    return ProvenanceEntry(
        article_id=article_id,
        source_part="word/document.xml",
        source_index=source_index,
        source_hash=hash_text(source_text),
        semantic_role=semantic_role,
        operation=operation,
        final_paragraph_index=final_paragraph_index,
        final_style_id=final_style_id,
    )
