from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document

MODULE_ROOT = Path(__file__).resolve().parents[1]
MARKERS_PATH = MODULE_ROOT / "resources" / "markers.json"

DEFAULT_ANNOTATION_MARKERS = [
    "Анотація",
    "Анотація:",
    "Анотація.",
    "Annotation",
    "Annotation:",
    "Abstract",
    "Abstract:",
]

DEFAULT_KEYWORD_MARKERS = [
    "Ключові слова",
    "Ключові слова:",
    "Keywords",
    "Keywords:",
    "Key words",
    "Key Words",
    "Key words:",
    "Key Words:",
]

DEFAULT_REFERENCE_MARKERS = [
    "Список використаних джерел",
    "Список використаних джерел:",
    "Література",
    "References",
    "References:",
    "List of references",
    "List of reference",
]

HEADING_HINT_RE = re.compile(
    r"(анотац|abstract|annotation|summary|реферат|ключов|keywords|key words|літератур|references|bibliography|джерел)",
    re.IGNORECASE,
)


def _load_list(key: str, fallback: list[str]) -> list[str]:
    try:
        data = json.loads(MARKERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return fallback
    if not isinstance(data, dict):
        return fallback
    values = data.get(key)
    if not isinstance(values, list):
        return fallback
    cleaned = [str(x).strip() for x in values if str(x).strip()]
    return cleaned or fallback


def _normalize_source(text: str) -> str:
    text = (text or "").replace("\u00a0", " ").lstrip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^\s*[IVXLCDM]+\s*[\.\)\-]?\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*\d+\s*[\.\)\-]?\s*", "", text)
    return text


def _match_marker(text: str, markers: list[str]) -> str | None:
    source = _normalize_source(text)
    lowered = source.lower()
    cleaned = [m.strip() for m in markers if isinstance(m, str) and m.strip()]
    cleaned.sort(key=len, reverse=True)
    for marker in cleaned:
        m_low = marker.lower()
        if lowered.startswith(m_low):
            return marker
        marker_base = re.sub(r"[\s\.\:\;\-–—]+$", "", marker)
        if marker_base and lowered.startswith(marker_base.lower()):
            return marker
    return None


def _looks_like_heading(text: str) -> bool:
    stripped = _normalize_source(text)
    if not stripped:
        return False
    if len(stripped) > 80:
        return False
    if not HEADING_HINT_RE.search(stripped):
        return False
    return True


def _collect_docs(folder: Path) -> list[Path]:
    return sorted([p for p in folder.rglob("*.docx") if p.is_file()])


def _resolve_search_roots(folder: Path) -> list[Path]:
    direct = folder / "Заявки"
    if direct.exists() and direct.is_dir():
        return [direct]
    nested = sorted([p for p in folder.rglob("Заявки") if p.is_dir()])
    if nested:
        return nested
    return [folder]


def audit_folder(folder: Path, output_dir: Path) -> dict:
    markers = _load_list("annotation_markers", DEFAULT_ANNOTATION_MARKERS)
    keyword_markers = _load_list("keyword_markers", DEFAULT_KEYWORD_MARKERS)
    reference_markers = _load_list("reference_markers", DEFAULT_REFERENCE_MARKERS)

    roots = _resolve_search_roots(folder)
    all_docs: list[Path] = []
    for root in roots:
        all_docs.extend(_collect_docs(root))
    per_doc = []
    total_marker_counts = Counter()
    marker_docs = defaultdict(set)
    candidate_counts = Counter()
    candidate_docs = defaultdict(set)

    for doc_path in all_docs:
        doc = Document(doc_path)
        doc_counts = Counter()
        candidates_local = Counter()
        for para in doc.paragraphs:
            text = (para.text or "").strip()
            if not text:
                continue
            hit = _match_marker(text, markers)
            if hit:
                doc_counts[f"annotation::{hit}"] += 1
                total_marker_counts[f"annotation::{hit}"] += 1
                marker_docs[f"annotation::{hit}"].add(doc_path.name)
                continue
            hit = _match_marker(text, keyword_markers)
            if hit:
                doc_counts[f"keywords::{hit}"] += 1
                total_marker_counts[f"keywords::{hit}"] += 1
                marker_docs[f"keywords::{hit}"].add(doc_path.name)
                continue
            hit = _match_marker(text, reference_markers)
            if hit:
                doc_counts[f"references::{hit}"] += 1
                total_marker_counts[f"references::{hit}"] += 1
                marker_docs[f"references::{hit}"].add(doc_path.name)
                continue

            if _looks_like_heading(text):
                cleaned = _normalize_source(text)
                candidates_local[cleaned] += 1
                candidate_counts[cleaned] += 1
                candidate_docs[cleaned].add(doc_path.name)

        per_doc.append(
            {
                "file": doc_path.name,
                "marker_counts": dict(doc_counts),
                "candidate_headings": dict(candidates_local),
            }
        )

    summary = {
        "folder": str(folder),
        "total_documents": len(all_docs),
        "documents_with_markers": len(
            {doc for docs in marker_docs.values() for doc in docs}
        ),
        "marker_counts_total": dict(total_marker_counts),
        "marker_documents": {
            key: sorted(list(value)) for key, value in marker_docs.items()
        },
        "candidate_headings_total": dict(candidate_counts),
        "candidate_documents": {
            key: sorted(list(value)) for key, value in candidate_docs.items()
        },
        "per_document": per_doc,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "annotation_markers_audit.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    log_path = output_dir / "annotation_markers_audit.log"
    lines = [
        f"total_documents: {summary['total_documents']}",
        f"documents_with_markers: {summary['documents_with_markers']}",
        "",
        "marker_counts_total:",
    ]
    for key, count in sorted(total_marker_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {key}: {count}")
    lines.append("")
    lines.append("candidate_headings_total:")
    for key, count in sorted(candidate_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"  {key}: {count}")
    log_path.write_text("\n".join(lines), encoding="utf-8")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit annotation/keywords/references markers in docx folder")
    parser.add_argument("folder", type=Path, help="Folder with docx files")
    parser.add_argument("--output", type=Path, default=None, help="Output directory for report/log")
    args = parser.parse_args()

    if not args.folder.exists():
        raise SystemExit("Folder not found")
    if not args.folder.is_dir():
        raise SystemExit("Folder is not a directory")
    out_dir = args.output or args.folder
    audit_folder(args.folder, out_dir)
    print(f"OK: {out_dir}")


if __name__ == "__main__":
    main()
