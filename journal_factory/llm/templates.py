from __future__ import annotations

import json
from typing import Any

from .chunking import Paragraph


PROMPT_VERSION = "journal-llm-classifier.v1"


def _user_payload(paragraphs: list[Paragraph], schema: dict[str, Any]) -> str:
    return json.dumps(
        {
            "task": "classify_paragraphs",
            "contract": {
                "return_json_only": True,
                "preserve_paragraph_ids_exactly": True,
                "preserve_order_exactly": True,
                "do_not_edit_source_text": True,
                "schema_version": "paragraph-classification.v1",
            },
            "schema": schema,
            "paragraphs": [
                {
                    "paragraph_id": paragraph.paragraph_id,
                    "text": paragraph.text,
                    "context_only": paragraph.context_only,
                }
                for paragraph in paragraphs
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def render_messages(
    paragraphs: list[Paragraph],
    *,
    schema: dict[str, Any],
    prompt_template: str,
) -> list[dict[str, str]]:
    if prompt_template not in {"auto_jinja", "manual_chatml"}:
        raise ValueError(f"unknown prompt_template: {prompt_template}")

    system = (
        "You are a local Journal Factory reviewer. Return strict JSON only. "
        "Do not edit source text. Preserve every paragraph_id exactly once and in order."
    )
    user_payload = _user_payload(paragraphs, schema)
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
