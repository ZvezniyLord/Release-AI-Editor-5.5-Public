from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"(?<![A-Za-z0-9_])/(?:mnt|home|Users|private|var/folders)/"),
]
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_PLACEHOLDERS = {"PENDING_FINAL_COMMIT_SHA_REPORTED_AFTER_PUSH", "PENDING", "TODO"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def handoff_schema_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "schemas" / "llm" / "handoff.schema.json"


def load_handoff_schema(root: Path | None = None) -> dict[str, Any]:
    return json.loads(handoff_schema_path(root).read_text(encoding="utf-8"))


def _walk(value: Any, path: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        findings: list[tuple[str, str]] = []
        for key, item in value.items():
            findings.extend(_walk(item, f"{path}.{key}"))
        return findings
    if isinstance(value, list):
        findings = []
        for index, item in enumerate(value):
            findings.extend(_walk(item, f"{path}[{index}]"))
        return findings
    if isinstance(value, str):
        findings = []
        if value in FORBIDDEN_PLACEHOLDERS:
            findings.append((path, "placeholder_value"))
        for pattern in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(value):
                findings.append((path, "absolute_path"))
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                findings.append((path, "secret_pattern"))
        return findings
    return []


def _json_path(path: tuple[Any, ...]) -> str:
    rendered = "$"
    for item in path:
        if isinstance(item, int):
            rendered += f"[{item}]"
        else:
            rendered += f".{item}"
    return rendered


def _is_relative_public_path(value: str) -> bool:
    return not value.startswith("/") and not re.match(r"^[A-Za-z]:\\", value) and ".." not in Path(value).parts


def validate_public_handoff(data: dict[str, Any], *, root: Path | None = None) -> list[dict[str, str]]:
    issues = [{"path": path, "issue": issue} for path, issue in _walk(data)]

    schema = load_handoff_schema(root)
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda err: list(err.path)):
        issues.append({"path": _json_path(tuple(error.path)), "issue": f"schema: {error.message}"})

    for sha_field in ("base_sha", "implementation_commit_sha"):
        value = data.get(sha_field)
        if isinstance(value, str) and not SHA_RE.match(value):
            issues.append({"path": f"$.{sha_field}", "issue": "invalid_sha_format"})
    report_commit_sha = data.get("report_commit_sha")
    if report_commit_sha is not None and (
        not isinstance(report_commit_sha, str) or not SHA_RE.match(report_commit_sha)
    ):
        issues.append({"path": "$.report_commit_sha", "issue": "invalid_sha_format"})

    for key, value in (data.get("report_paths") or {}).items():
        if not isinstance(value, str) or not _is_relative_public_path(value):
            issues.append({"path": f"$.report_paths.{key}", "issue": "invalid_report_path"})

    for index, record in enumerate(data.get("test_records") or []):
        if not record.get("command"):
            issues.append({"path": f"$.test_records[{index}].command", "issue": "missing_test_command"})
        if record.get("result") not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}:
            issues.append({"path": f"$.test_records[{index}].result", "issue": "invalid_test_result"})

    return issues


def validate_public_handoff_file(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return [{"path": "$", "issue": "handoff_must_be_object"}]
    return validate_public_handoff(data, root=repo_root())
