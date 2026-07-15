from __future__ import annotations

import posixpath
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from .ooxml import REL, REL_NS


def relationship_part_for(part_name: str) -> str:
    folder, filename = part_name.rsplit("/", 1)
    return f"{folder}/_rels/{filename}.rels"


def resolve_part_target(base_part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    base_folder = base_part.rsplit("/", 1)[0] if "/" in base_part else ""
    return posixpath.normpath(posixpath.join(base_folder, target))


def rels_base_part(rels_name: str) -> str:
    if rels_name == "_rels/.rels":
        return ""
    folder, filename = rels_name.rsplit("/_rels/", 1)
    return f"{folder}/{filename.removesuffix('.rels')}"


def missing_relationship_targets(docx_path: Path) -> list[dict[str, str]]:
    missing = []
    with zipfile.ZipFile(docx_path) as archive:
        names = set(archive.namelist())
        for rels_name in sorted(name for name in names if name.endswith(".rels")):
            base_part = rels_base_part(rels_name)
            root = ET.fromstring(archive.read(rels_name))
            for rel in root.findall(f"{REL}Relationship"):
                if rel.get("TargetMode") == "External":
                    continue
                target = rel.get("Target")
                if not target:
                    continue
                part = resolve_part_target(base_part, target)
                if part not in names:
                    missing.append(
                        {
                            "rels_part": rels_name,
                            "relationship_id": rel.get("Id", ""),
                            "target": target,
                            "resolved_part": part,
                            "type": rel.get("Type", ""),
                        }
                    )
    return missing


def direct_formatting_histogram(findings: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: Counter[tuple[str, str, str, bool]] = Counter()
    articles_by_group: dict[tuple[str, str, str, bool], set[str]] = {}
    for item in findings:
        key = (
            str(item.get("rule_code", "")),
            str(item.get("property", "")),
            str(item.get("semantic_role", "")),
            bool(item.get("safe_to_auto_fix", False)),
        )
        grouped[key] += 1
        articles_by_group.setdefault(key, set()).add(str(item.get("article_id", "")))
    rows = []
    for (rule_code, prop, role, safe), count in sorted(grouped.items()):
        rows.append(
            {
                "rule_code": rule_code,
                "property": prop,
                "semantic_role": role,
                "article_count": len(articles_by_group[(rule_code, prop, role, safe)] - {""}),
                "finding_count": count,
                "safe_to_auto_fix": safe,
            }
        )
    return rows


__all__ = ["REL_NS", "direct_formatting_histogram", "missing_relationship_targets", "relationship_part_for", "resolve_part_target"]
