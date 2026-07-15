from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


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
        for pattern in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(value):
                findings.append((path, "absolute_path"))
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                findings.append((path, "secret_pattern"))
        return findings
    return []


def validate_public_handoff(data: dict[str, Any]) -> list[dict[str, str]]:
    return [{"path": path, "issue": issue} for path, issue in _walk(data)]


def validate_public_handoff_file(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return [{"path": "$", "issue": "handoff_must_be_object"}]
    return validate_public_handoff(data)
