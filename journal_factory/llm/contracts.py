from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


class ModelResponseError(ValueError):
    """Model output is not acceptable for deterministic post-processing."""


class SchemaValidationError(ModelResponseError):
    """Model output failed the classifier JSON schema."""


class IDContractError(ModelResponseError):
    """Model output did not exactly preserve expected paragraph IDs."""


class ModelStateDisagreementError(ModelResponseError):
    """Model state_update disagrees with deterministic worker state."""


FORBIDDEN_RESPONSE_KEYS = {"original_text", "text", "block_id"}

V1_BLOCK_TYPES = {
    "section",
    "doi",
    "udc",
    "empty_paragraph",
    "author",
    "author_status",
    "affiliation",
    "city_country",
    "title",
    "annotation",
    "keywords",
    "main_text",
    "table_caption",
    "figure_caption",
    "formula",
    "references_heading",
    "references_item",
    "service_data",
    "unknown",
}

STATE_KEYS = {
    "section_found",
    "doi_found",
    "udc_found",
    "authors_found",
    "author_status_found",
    "affiliation_found",
    "city_country_found",
    "title_found",
    "annotation_found",
    "keywords_found",
    "body_started",
    "references_started",
    "references_finished",
    "service_data_found",
}

BLOCK_TO_STATE = {
    "section": "section_found",
    "doi": "doi_found",
    "udc": "udc_found",
    "author": "authors_found",
    "author_status": "author_status_found",
    "affiliation": "affiliation_found",
    "city_country": "city_country_found",
    "title": "title_found",
    "annotation": "annotation_found",
    "keywords": "keywords_found",
    "main_text": "body_started",
    "table_caption": "body_started",
    "figure_caption": "body_started",
    "formula": "body_started",
    "references_heading": "references_started",
    "references_item": "references_started",
    "service_data": "service_data_found",
}


@dataclass(frozen=True)
class Classification:
    block_type: str
    paragraph_ids: tuple[str, ...]
    confidence: float
    evidence: tuple[str, ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def journal_builder_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / "skills" / "journal_builder"


def skill_schema_path(
    root: Path | None = None,
    *,
    version: str = "v1",
    schema_name: str = "paragraph_classifier_output",
) -> Path:
    return journal_builder_root(root) / "schemas" / f"{schema_name}.{version}.schema.json"


def load_skill_schema(
    root: Path | None = None,
    *,
    version: str = "v1",
    schema_name: str = "paragraph_classifier_output",
) -> dict[str, Any]:
    return json.loads(
        skill_schema_path(root, version=version, schema_name=schema_name).read_text(encoding="utf-8")
    )


def stable_text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_strict_json(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaValidationError("model output is not strict JSON") from exc
    if not isinstance(payload, dict):
        raise SchemaValidationError("model output must be a JSON object")
    return payload


def _json_path(path: tuple[Any, ...]) -> str:
    if not path:
        return "$"
    rendered = "$"
    for item in path:
        if isinstance(item, int):
            rendered += f"[{item}]"
        else:
            rendered += f".{item}"
    return rendered


def validate_schema(payload: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    active_schema = schema or load_skill_schema()
    validator = Draft202012Validator(active_schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if errors:
        first = errors[0]
        raise SchemaValidationError(f"{_json_path(tuple(first.path))}: {first.message}") from first


def reject_forbidden_response_keys(value: Any, path: tuple[Any, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_RESPONSE_KEYS:
                raise SchemaValidationError(f"{_json_path(path + (key,))}: forbidden response key")
            reject_forbidden_response_keys(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_forbidden_response_keys(child, path + (index,))


def _flatten_block_ids(payload: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for block in payload.get("blocks", []):
        ids.extend(block.get("paragraph_ids", []))
    return ids


def validate_exact_id_contract(
    payload: dict[str, Any],
    expected_ids: list[str],
    *,
    context_only_ids: list[str] | None = None,
) -> None:
    actual_ids = _flatten_block_ids(payload)
    context_ids = set(context_only_ids or [])
    leaked_context = [pid for pid in actual_ids if pid in context_ids]
    if leaked_context:
        raise IDContractError(f"context-only paragraph IDs returned: {leaked_context}")

    duplicates = sorted({pid for pid in actual_ids if actual_ids.count(pid) > 1})
    if duplicates:
        raise IDContractError(f"duplicate paragraph IDs: {duplicates}")

    missing = [pid for pid in expected_ids if pid not in actual_ids]
    extra = [pid for pid in actual_ids if pid not in expected_ids]
    if missing or extra:
        raise IDContractError(f"ID mismatch missing={missing} extra={extra}")
    if actual_ids != expected_ids:
        raise IDContractError("paragraph IDs were reordered")


def deterministic_state_transition(
    input_state: dict[str, bool] | None,
    blocks: list[dict[str, Any]],
) -> dict[str, bool]:
    state = {key: bool((input_state or {}).get(key, False)) for key in STATE_KEYS}
    for block in blocks:
        state_key = BLOCK_TO_STATE.get(block.get("block_type"))
        if state_key:
            state[state_key] = True
        if block.get("block_type") == "references_item":
            state["references_started"] = True
    return state


def validate_model_state_update(
    payload: dict[str, Any],
    *,
    input_state: dict[str, bool] | None = None,
) -> dict[str, bool]:
    deterministic = deterministic_state_transition(input_state, payload.get("blocks", []))
    model_update = payload.get("state_update", {})
    disagreements: dict[str, dict[str, bool]] = {}
    for key, model_value in model_update.items():
        if key in deterministic and bool(model_value) != bool(deterministic[key]):
            disagreements[key] = {
                "model": bool(model_value),
                "deterministic": bool(deterministic[key]),
            }
    if disagreements:
        raise ModelStateDisagreementError(f"MODEL_STATE_DISAGREEMENT: {disagreements}")
    return deterministic


def validate_source_hash(payload: dict[str, Any], expected_source_hash: str | None = None) -> None:
    if expected_source_hash and payload.get("source_hash") != expected_source_hash:
        raise IDContractError("source_hash changed or did not match request")


def validate_model_payload(
    payload: dict[str, Any],
    *,
    expected_ids: list[str],
    context_only_ids: list[str] | None = None,
    expected_source_hash: str | None = None,
    input_state: dict[str, bool] | None = None,
    schema: dict[str, Any] | None = None,
) -> list[Classification]:
    reject_forbidden_response_keys(payload)
    validate_schema(payload, schema=schema)
    validate_exact_id_contract(payload, expected_ids, context_only_ids=context_only_ids)
    validate_source_hash(payload, expected_source_hash)
    validate_model_state_update(payload, input_state=input_state)
    return [
        Classification(
            block_type=block["block_type"],
            paragraph_ids=tuple(block["paragraph_ids"]),
            confidence=float(block["confidence"]),
            evidence=tuple(block["evidence"]),
        )
        for block in payload["blocks"]
    ]


def validate_model_text(
    text: str,
    *,
    expected_ids: list[str],
    context_only_ids: list[str] | None = None,
    expected_source_hash: str | None = None,
    input_state: dict[str, bool] | None = None,
    schema: dict[str, Any] | None = None,
) -> list[Classification]:
    payload = parse_strict_json(text)
    return validate_model_payload(
        payload,
        expected_ids=expected_ids,
        context_only_ids=context_only_ids,
        expected_source_hash=expected_source_hash,
        input_state=input_state,
        schema=schema,
    )
