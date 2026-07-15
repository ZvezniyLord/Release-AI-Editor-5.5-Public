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


def _user_payload(paragraphs: list[Paragraph]) -> str:
    payload: dict[str, Any] = {
        "contract_version": "paragraph_classifier_input.v1",
        "article_id": "SYN-A001",
        "source_hash": SOURCE_HASH,
        "language": "uk",
        "state": {},
        "schema_id": load_skill_schema()["$id"],
        "paragraphs": [
            {
                "paragraph_id": paragraph.paragraph_id,
                "text": paragraph.text,
                "context_only": paragraph.context_only,
            }
            for paragraph in paragraphs
        ],
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
    user_payload = _user_payload(paragraphs)
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
