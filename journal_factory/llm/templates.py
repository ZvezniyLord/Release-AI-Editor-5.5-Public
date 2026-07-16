from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .chunking import Paragraph
from .contracts import journal_builder_root, load_skill_schema
from .synthetic import SOURCE_HASH


PROMPT_VERSION = "paragraph-classifier-v1"


def prompt_path(root: Path | None = None, *, version: str = "v1") -> Path:
    return journal_builder_root(root) / "prompts" / "paragraph_classifier" / version / "system.txt"


def load_system_prompt(root: Path | None = None, *, version: str = "v1") -> str:
    return prompt_path(root, version=version).read_text(encoding="utf-8")


def _paragraph_payload(paragraph: Paragraph) -> dict[str, Any]:
    return {
        "paragraph_id": paragraph.paragraph_id,
        "text": paragraph.text,
        "context_only": paragraph.context_only,
    }


def _paragraph_payload_v1_1(paragraph: Paragraph) -> dict[str, Any]:
    return {
        "paragraph_id": paragraph.paragraph_id,
        "text": paragraph.text,
        "is_empty": paragraph.text.strip() == "",
    }


def _user_payload(paragraphs: list[Paragraph], *, prompt_version: str = "v1") -> str:
    if prompt_version == "v1.1":
        source_paragraphs = [paragraph for paragraph in paragraphs if not paragraph.context_only]
        context_paragraphs = [paragraph for paragraph in paragraphs if paragraph.context_only]
        payload: dict[str, Any] = {
            "contract_version": "paragraph_classifier_input.v1.1-candidate",
            "article_id": "SYN-A001",
            "source_hash": SOURCE_HASH,
            "language": "uk",
            "state": {},
            "schema_id": load_skill_schema()["$id"],
            "source_paragraphs": [_paragraph_payload_v1_1(paragraph) for paragraph in source_paragraphs],
            "context_paragraphs": [_paragraph_payload_v1_1(paragraph) for paragraph in context_paragraphs],
            "source_id_contract": {
                "required_source_ids": [paragraph.paragraph_id for paragraph in source_paragraphs],
                "forbidden_context_ids": [paragraph.paragraph_id for paragraph in context_paragraphs],
            },
            "deterministic_markers": {
                "doi": [],
                "udc": [],
                "orcid": [],
                "reference_candidates": [],
            },
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    payload: dict[str, Any] = {
        "contract_version": "paragraph_classifier_input.v1",
        "article_id": "SYN-A001",
        "source_hash": SOURCE_HASH,
        "language": "uk",
        "state": {},
        "schema_id": load_skill_schema()["$id"],
        "paragraphs": [_paragraph_payload(paragraph) for paragraph in paragraphs],
        "deterministic_markers": {
            "doi": [],
            "udc": [],
            "orcid": [],
            "reference_candidates": [],
        },
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def render_messages(
    paragraphs: list[Paragraph],
    *,
    schema: dict[str, Any] | None = None,
    prompt_template: str,
    prompt_version: str = "v1",
) -> list[dict[str, str]]:
    if prompt_template not in {"auto_jinja", "manual_chatml"}:
        raise ValueError(f"unknown prompt_template: {prompt_template}")

    system = load_system_prompt(version=prompt_version)
    user_payload = _user_payload(paragraphs, prompt_version=prompt_version)
    if prompt_template == "auto_jinja":
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_payload},
        ]
    manual = (
        "<|im_start|>system\n"
        f"{system}\n"
        "<|im_end|>\n"
        "<|im_start|>user\n"
        f"{user_payload}\n"
        "<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    return [{"role": "user", "content": manual}]
