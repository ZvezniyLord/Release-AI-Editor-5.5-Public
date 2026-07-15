from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ModelResponseError(ValueError):
    """Model output is not acceptable for deterministic post-processing."""


class SchemaValidationError(ModelResponseError):
    """Model output failed the classifier JSON schema."""


class IDContractError(ModelResponseError):
    """Model output did not exactly preserve expected paragraph IDs."""


ALLOWED_ROLES = {
    "empty",
    "doi",
    "udc",
    "orcid",
    "author",
    "institution",
    "author_status",
    "title",
    "annotation",
    "keywords",
    "body",
    "table_caption",
    "figure_caption",
    "formula",
    "references_heading",
    "references_item",
    "unknown",
    "context_only",
}


@dataclass(frozen=True)
class Classification:
    paragraph_id: str
    role: str
    confidence: float
    evidence: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def skill_schema_path(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "skills" / "journal-llm-governance" / "schemas" / "paragraph-classification.schema.json"


def load_skill_schema(root: Path | None = None) -> dict[str, Any]:
    return json.loads(skill_schema_path(root).read_text(encoding="utf-8"))


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


def validate_schema(payload: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    """Small local validator for the schema committed with this repo.

    This avoids a runtime dependency while still using the versioned JSON
    Schema as the public contract source.
    """

    required_top = {"schema_version", "prompt_version", "paragraphs"}
    missing_top = required_top - set(payload)
    if missing_top:
        raise SchemaValidationError(f"missing top-level keys: {sorted(missing_top)}")
    if not isinstance(payload["schema_version"], str) or not payload["schema_version"]:
        raise SchemaValidationError("schema_version must be a non-empty string")
    if payload["schema_version"] != "paragraph-classification.v1":
        raise SchemaValidationError("unsupported schema_version")
    if not isinstance(payload["prompt_version"], str) or not payload["prompt_version"]:
        raise SchemaValidationError("prompt_version must be a non-empty string")
    paragraphs = payload["paragraphs"]
    if not isinstance(paragraphs, list):
        raise SchemaValidationError("paragraphs must be a list")
    for index, item in enumerate(paragraphs):
        if not isinstance(item, dict):
            raise SchemaValidationError(f"paragraphs[{index}] must be an object")
        required = {"paragraph_id", "role", "confidence", "evidence"}
        missing = required - set(item)
        if missing:
            raise SchemaValidationError(f"paragraphs[{index}] missing keys: {sorted(missing)}")
        if not isinstance(item["paragraph_id"], str) or not item["paragraph_id"]:
            raise SchemaValidationError(f"paragraphs[{index}].paragraph_id must be non-empty string")
        if item["role"] not in ALLOWED_ROLES:
            raise SchemaValidationError(f"paragraphs[{index}].role is not allowed: {item['role']}")
        confidence = item["confidence"]
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            raise SchemaValidationError(f"paragraphs[{index}].confidence must be between 0 and 1")
        if not isinstance(item["evidence"], str):
            raise SchemaValidationError(f"paragraphs[{index}].evidence must be a string")
        if "source_text_sha256" in item and not isinstance(item["source_text_sha256"], str):
            raise SchemaValidationError(f"paragraphs[{index}].source_text_sha256 must be a string")


def validate_exact_id_contract(payload: dict[str, Any], expected_ids: list[str]) -> None:
    actual_ids = [item["paragraph_id"] for item in payload.get("paragraphs", [])]
    duplicates = sorted({pid for pid in actual_ids if actual_ids.count(pid) > 1})
    if duplicates:
        raise IDContractError(f"duplicate paragraph IDs: {duplicates}")
    missing = [pid for pid in expected_ids if pid not in actual_ids]
    extra = [pid for pid in actual_ids if pid not in expected_ids]
    if missing or extra:
        raise IDContractError(f"ID mismatch missing={missing} extra={extra}")
    if actual_ids != expected_ids:
        raise IDContractError("paragraph IDs were reordered")


def validate_source_hashes(payload: dict[str, Any], source_hashes: dict[str, str]) -> None:
    for item in payload.get("paragraphs", []):
        expected_hash = source_hashes.get(item["paragraph_id"])
        reported_hash = item.get("source_text_sha256")
        if expected_hash and reported_hash and expected_hash != reported_hash:
            raise IDContractError(f"source text hash changed for {item['paragraph_id']}")


def validate_model_payload(
    payload: dict[str, Any],
    *,
    expected_ids: list[str],
    source_hashes: dict[str, str] | None = None,
    schema: dict[str, Any] | None = None,
) -> list[Classification]:
    validate_schema(payload, schema=schema)
    validate_exact_id_contract(payload, expected_ids)
    if source_hashes:
        validate_source_hashes(payload, source_hashes)
    return [
        Classification(
            paragraph_id=item["paragraph_id"],
            role=item["role"],
            confidence=float(item["confidence"]),
            evidence=item["evidence"],
        )
        for item in payload["paragraphs"]
    ]


def validate_model_text(
    text: str,
    *,
    expected_ids: list[str],
    source_hashes: dict[str, str] | None = None,
    schema: dict[str, Any] | None = None,
) -> list[Classification]:
    payload = parse_strict_json(text)
    return validate_model_payload(
        payload,
        expected_ids=expected_ids,
        source_hashes=source_hashes,
        schema=schema,
    )
