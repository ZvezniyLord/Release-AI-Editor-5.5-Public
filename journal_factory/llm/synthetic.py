from __future__ import annotations

import re
from typing import Any

from .chunking import Paragraph
from .contracts import stable_text_sha256


SCHEMA_VERSION = "paragraph-classification.v1"
PROMPT_VERSION = "journal-llm-classifier.v1"


def synthetic_paragraphs() -> list[Paragraph]:
    return [
        Paragraph("P000", ""),
        Paragraph("P001", "DOI: 10.0000/synthetic.doi"),
        Paragraph("P002", "UDC 004.8:001.89"),
        Paragraph("P003", "ORCID: TEST-ORCID"),
        Paragraph("P004", "Ada Testenko, Borys Example"),
        Paragraph("P005", "Synthetic Institute named after Example Scholar"),
        Paragraph("P006", "PhD student, synthetic department"),
        Paragraph("P007", "Synthetic Article Title About Local Models"),
        Paragraph("P008", "Annotation. This paragraph describes a synthetic article."),
        Paragraph("P009", "Keywords: synthetic data; local LLM; validation"),
        Paragraph("P010", "Main body paragraph with deterministic non-private text."),
        Paragraph("P011", "Table 1. Synthetic benchmark matrix"),
        Paragraph("P012", "Figure 1. Synthetic architecture diagram"),
        Paragraph("P013", "E = mc^2 + synthetic variable x_i"),
        Paragraph("P014", "References"),
        Paragraph("P015", "1. Example A. Synthetic reference item. 2026."),
        Paragraph("P016", "Ambiguous heading-like fragment"),
        Paragraph("P017", "Context paragraph for neighbor disambiguation", context_only=True),
    ]


def classify_role(text: str, *, context_only: bool = False) -> str:
    stripped = text.strip()
    lowered = stripped.lower()
    if context_only:
        return "context_only"
    if not stripped:
        return "empty"
    if lowered.startswith("doi"):
        return "doi"
    if lowered.startswith("udc"):
        return "udc"
    if "orcid" in lowered:
        return "orcid"
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
        return "institution"
    if "title" in stripped and len(stripped.split()) <= 8:
        return "title"
    if " = " in stripped or "^" in stripped:
        return "formula"
    if "," in stripped and len(stripped.split()) <= 6:
        return "author"
    if "ambiguous" in lowered:
        return "unknown"
    return "body"


def expected_payload(paragraphs: list[Paragraph]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "paragraphs": [
            {
                "paragraph_id": paragraph.paragraph_id,
                "role": classify_role(paragraph.text, context_only=paragraph.context_only),
                "confidence": 1.0 if not paragraph.context_only else 0.9,
                "evidence": "synthetic deterministic classifier",
                "source_text_sha256": stable_text_sha256(paragraph.text),
            }
            for paragraph in paragraphs
        ],
    }


def malformed_payload_cases(paragraphs: list[Paragraph]) -> dict[str, Any]:
    base = expected_payload(paragraphs)
    missing = expected_payload(paragraphs)
    missing["paragraphs"] = missing["paragraphs"][1:]

    extra = expected_payload(paragraphs)
    extra["paragraphs"].append(
        {
            "paragraph_id": "P999",
            "role": "unknown",
            "confidence": 0.1,
            "evidence": "extra id",
        }
    )

    duplicate = expected_payload(paragraphs)
    duplicate["paragraphs"].append(dict(duplicate["paragraphs"][0]))

    reordered = expected_payload(paragraphs)
    reordered["paragraphs"] = list(reversed(reordered["paragraphs"]))

    changed_hash = expected_payload(paragraphs)
    changed_hash["paragraphs"][0]["source_text_sha256"] = "0" * 64

    return {
        "base": base,
        "missing_id": missing,
        "extra_id": extra,
        "duplicate_id": duplicate,
        "reordered_ids": reordered,
        "changed_hash": changed_hash,
    }
