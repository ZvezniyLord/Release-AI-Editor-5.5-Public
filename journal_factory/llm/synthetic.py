from __future__ import annotations

import re
from typing import Any

from .chunking import Paragraph
from .contracts import deterministic_state_transition, stable_text_sha256


SOURCE_HASH = stable_text_sha256("journal-factory-llm-synthetic-source-v1")
PROMPT_VERSION = "paragraph-classifier-v1"


def synthetic_paragraphs() -> list[Paragraph]:
    return [
        Paragraph("P000", ""),
        Paragraph("P001", "DOI: 10.0000/synthetic.doi"),
        Paragraph("P002", "UDC 004.8:001.89"),
        Paragraph("P003", "ORCID: TEST-ORCID"),
        Paragraph("P004", "Ada Testenko, Borys Example"),
        Paragraph("P005", "Synthetic Institute named after Example Scholar"),
        Paragraph("P006", "Kyiv, Ukraine"),
        Paragraph("P007", "PhD student, synthetic department"),
        Paragraph("P008", "Synthetic Article Title About Local Models"),
        Paragraph("P009", "Annotation. This paragraph describes a synthetic article."),
        Paragraph("P010", "Keywords: synthetic data; local LLM; validation"),
        Paragraph("P011", "Main body paragraph with deterministic non-private text."),
        Paragraph("P012", "Table 1. Synthetic benchmark matrix"),
        Paragraph("P013", "Figure 1. Synthetic architecture diagram"),
        Paragraph("P014", "E = mc^2 + synthetic variable x_i"),
        Paragraph("P015", "References"),
        Paragraph("P016", "1. Example A. Synthetic reference item. 2026."),
        Paragraph("P017", "Ambiguous heading-like fragment"),
        Paragraph("P018", "Context paragraph for neighbor disambiguation", context_only=True),
    ]


def classify_block_type(text: str, *, context_only: bool = False) -> str | None:
    stripped = text.strip()
    lowered = stripped.lower()
    if context_only:
        return None
    if not stripped:
        return "empty_paragraph"
    if lowered.startswith("doi"):
        return "doi"
    if lowered.startswith("udc"):
        return "udc"
    if "orcid" in lowered:
        return "service_data"
    if lowered.startswith("annotation"):
        return "annotation"
    if lowered.startswith("keywords"):
        return "keywords"
    if lowered.startswith("table "):
        return "table_caption"
    if lowered.startswith("figure "):
        return "figure_caption"
    if lowered == "references":
        return "references_heading"
    if re.match(r"^\d+\.\s", stripped):
        return "references_item"
    if "phd student" in lowered or "student" in lowered:
        return "author_status"
    if "institute" in lowered or "department" in lowered:
        return "affiliation"
    if "title" in lowered and len(stripped.split()) <= 8:
        return "title"
    if re.match(r"^[A-Z][A-Za-z .-]+,\s*[A-Z][A-Za-z .-]+$", stripped) and any(
        country in lowered for country in ("ukraine", "poland", "germany", "france")
    ):
        return "city_country"
    if " = " in stripped or "^" in stripped:
        return "formula"
    if "," in stripped and len(stripped.split()) <= 6:
        return "author"
    if "ambiguous" in lowered:
        return "unknown"
    return "main_text"


def expected_payload(paragraphs: list[Paragraph]) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    for paragraph in paragraphs:
        block_type = classify_block_type(paragraph.text, context_only=paragraph.context_only)
        if block_type is None:
            continue
        blocks.append(
            {
                "block_type": block_type,
                "paragraph_ids": [paragraph.paragraph_id],
                "confidence": 1.0,
                "text_excerpt": paragraph.text[:120],
                "evidence": ["synthetic deterministic classifier"],
            }
        )
    state_update = deterministic_state_transition(None, blocks)
    return {
        "article_id": "SYN-A001",
        "source_hash": SOURCE_HASH,
        "model": "synthetic-static-json",
        "prompt_version": PROMPT_VERSION,
        "fragment_status": "accepted",
        "state_update": state_update,
        "blocks": blocks,
        "problems": [],
        "next_action": "continue",
    }


def malformed_payload_cases(paragraphs: list[Paragraph]) -> dict[str, Any]:
    base = expected_payload(paragraphs)
    missing = expected_payload(paragraphs)
    missing["blocks"] = missing["blocks"][1:]

    extra = expected_payload(paragraphs)
    extra["blocks"].append(
        {
            "block_type": "unknown",
            "paragraph_ids": ["P999"],
            "confidence": 0.1,
            "evidence": ["extra id"],
        }
    )

    duplicate = expected_payload(paragraphs)
    duplicate["blocks"].append(dict(duplicate["blocks"][0]))

    reordered = expected_payload(paragraphs)
    reordered["blocks"] = list(reversed(reordered["blocks"]))

    context_leak = expected_payload(paragraphs)
    context_leak["blocks"].append(
        {
            "block_type": "unknown",
            "paragraph_ids": ["P018"],
            "confidence": 0.1,
            "evidence": ["context id leaked"],
        }
    )

    changed_hash = expected_payload(paragraphs)
    changed_hash["source_hash"] = "0" * 64

    forbidden_text = expected_payload(paragraphs)
    forbidden_text["blocks"][0]["text"] = "forbidden source text field"

    old_role_name = expected_payload(paragraphs)
    old_role_name["blocks"][0]["block_type"] = "empty"

    orcid_type = expected_payload(paragraphs)
    orcid_type["blocks"][3]["block_type"] = "orcid"

    state_disagreement = expected_payload(paragraphs)
    state_disagreement["state_update"]["title_found"] = False

    return {
        "base": base,
        "missing_id": missing,
        "extra_id": extra,
        "duplicate_id": duplicate,
        "reordered_ids": reordered,
        "context_only_id": context_leak,
        "changed_hash": changed_hash,
        "forbidden_text": forbidden_text,
        "old_role_name": old_role_name,
        "orcid_type": orcid_type,
        "state_disagreement": state_disagreement,
    }
