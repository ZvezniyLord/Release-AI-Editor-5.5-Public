from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pythoncom
import win32com.client
from win32com.client import constants
import tkinter as tk
from tkinter import messagebox

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
MARKERS_PATH = ROOT_DIR / "resources" / "markers.json"

from word_com import start_word_app, open_document, shutdown_word_app


UDC_RE = re.compile(r"\b(УДК|UDC|UDK)\b", re.IGNORECASE)
UDC_PREFIX_RE = re.compile(r"^(УДК|UDC|UDK)\s*[:.]*\s*", re.IGNORECASE)
DOI_RE = re.compile(r"^\s*(doi\s*[:\s]|https?\s*:\s*/\s*/\s*doi\.org/)", re.IGNORECASE)
BROKEN_HTTP_LINK_RE = re.compile(r"\b(https?)\s*:\s*/\s*/", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
NOT_AUTHOR_KEYWORDS: list[str] = [
    "університет",
    "университет",
    "university",
    "інститут",
    "институт",
    "institute",
    "академ",
    "academy",
    "faculty",
    "факультет",
    "кафедр",
    "department",
    "college",
    "school",
    "center",
    "centre",
    "research",
    "laboratory",
    "lab",
    "ministry",
    "компан",
    "company",
    "llc",
    "ltd",
    "gmbh",
    "corp",
    "corporation",
    "association",
    "доктор",
    "кандидат",
    "phd",
    "dr.",
    "professor",
    "доцент",
    "аспірант",
    "студент",
    "student",
    "викладач",
    "assistant",
    "associate",
    "senior",
    "head",
    "україна",
    "ukraine",
]
SECTION_TITLES: set[str] = set()
INTERACTIVE_REVIEW = False
PAGE_SCAN_LIMIT = 10

DEFAULT_CASE_RULES = {
    "capitalized": {
        "uk": {
            "phrases": [
                "Майстер спорту України",
                "Заслужений тренер України",
            ],
            "words": [],
        },
        "en": {
            "phrases": [],
            "words": [],
        },
    },
    "lowercase": {
        "uk": {
            "phrases": [
                "кандидат наук",
                "доктор наук",
            ],
            "words": [
                "студент",
                "студентка",
                "здобувач",
                "аспірант",
                "аспірантка",
                "магістрант",
                "магістрантка",
                "слухач",
                "учень",
                "старшокласник",
                "старшокласниця",
                "доцент",
                "професор",
            ],
        },
        "en": {
            "phrases": [
                "associate professor",
                "assistant professor",
                "full professor",
                "postgraduate student",
                "doctoral student",
                "phd student",
                "senior lecturer",
                "lecturer",
                "research fellow",
                "research associate",
            ],
            "words": [],
        },
    },
}
CASE_RULES = json.loads(json.dumps(DEFAULT_CASE_RULES))


def normalize_url_protocol_spacing(line: str) -> str:
    return BROKEN_HTTP_LINK_RE.sub(lambda match: f"{match.group(1).lower()}://", line or "")


def is_narrow(p) -> bool:
    text = (p.Range.Text or "").strip()
    if not text:
        return False
    if len(text) > 140:
        return False
    lines = text.split("\r")
    avg_len = sum(len(l) for l in lines) / len(lines)
    return avg_len < 90


def is_left_block(p) -> bool:
    try:
        return float(p.LeftIndent) < 20
    except Exception:
        return False


def is_body(p) -> bool:
    try:
        return int(p.Alignment) == constants.wdAlignParagraphJustify
    except Exception:
        return False


def looks_like_header(block: list[str]) -> bool:
    text = " ".join(block).lower()
    score = 0
    if "удк" in text or "udc" in text or "udk" in text or "doi" in text:
        score += 2
    if "універс" in text:
        score += 1
    if "м." in text:
        score += 1
    name_hits = 0
    for line in block:
        raw_line = line
        line = fix_title_case(normalize_line(raw_line))
        name_candidate = normalize_name_line(raw_line)
        if is_name(name_candidate):
            name_hits += 1
    if name_hits >= 1 and score < 2:
        score = 2
    return score >= 2


def normalize_line(line: str) -> str:
    line = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", line)
    line = line.replace("..", ".")
    line = re.sub(r"\s+", " ", line)
    line = line.strip()
    line = line.strip(",")
    line = re.sub(r"\s+([,.;:])", r"\1", line)
    line = re.sub(r"([,;:])([^\s])", r"\1 \2", line)
    line = normalize_url_protocol_spacing(line)
    return line


def normalize_name_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    # Keep '*' in names: it is a semantic marker (deceased person).
    line = re.sub(r"^[\-\–\—\•\·]+\s*", "", line)
    line = line.rstrip(",.")
    return line.rstrip()


def strip_non_author_prefix(line: str) -> str:
    # For affiliation/position lines in header, remove list-like dash/bullet prefix.
    return re.sub(r"^[\-\–\—\•\·]+\s*", "", line or "")


def make_key(line: str) -> str:
    return normalize_line(line).casefold()


def is_section_title(line: str) -> bool:
    if not SECTION_TITLES:
        return False
    return make_key(line) in SECTION_TITLES


def fix_title_case(line: str) -> str:
    changed = line
    changed = apply_case_rules(changed, "capitalized")
    changed = apply_case_rules(changed, "lowercase")
    return changed


def normalize_udc_line(line: str) -> str:
    line = line.replace("..", ".")
    line = re.sub(r"\s+", " ", line).strip()
    line = normalize_url_protocol_spacing(line)
    match = UDC_PREFIX_RE.match(line)
    if not match:
        return line.rstrip(",").rstrip()
    prefix = match.group(1)
    if prefix.upper() == "UDK":
        prefix = "UDC"
    rest = line[match.end():].strip()
    return f"{prefix} {rest}".strip().rstrip(",")


def is_udc_like(line: str) -> bool:
    value = (line or "").strip()
    return bool(UDC_RE.search(value) or DOI_RE.search(value))


def is_name(line: str) -> bool:
    low = line.lower()
    if is_section_title(line):
        return False
    if "ukraine" in low or "україна" in low:
        return False
    if "м." in low:
        return False
    if any(k in low for k in NOT_AUTHOR_KEYWORDS):
        return False
    if any(ch.isdigit() for ch in line):
        return False
    words = [w for w in line.replace(",", " ").split() if w]
    if not (2 <= len(words) <= 3):
        return False

    def clean_token(token: str) -> str:
        return token.strip("*").strip()

    def is_initial(token: str) -> bool:
        token = clean_token(token)
        return bool(re.match(r"^[A-ZА-ЯІЇЄҐ]\.?$", token))

    def is_name_word(token: str) -> bool:
        token = clean_token(token)
        return bool(re.match(r"^[A-ZА-ЯІЇЄҐ][A-Za-zА-Яа-яІЇЄҐґіїє'’ʼ\\-]+$", token))

    return all(is_initial(w) or is_name_word(w) for w in words)


def is_section_style(paragraph) -> bool:
    try:
        style = paragraph.Range.Style
        try:
            name = style.NameLocal or ""
        except Exception:
            name = str(style)
        name_low = name.lower()
        return "section" in name_low or "секц" in name_low
    except Exception:
        return False


def is_title_style(paragraph) -> bool:
    try:
        style = paragraph.Range.Style
        try:
            name = style.NameLocal or ""
        except Exception:
            name = str(style)
        normalized = re.sub(r"[\s_-]+", "", name).casefold()
        return normalized in {"назва1", "title1"}
    except Exception:
        return False


def ask_confirm_batch(candidates: list[str]) -> tuple[set[str], set[str], bool]:
    if not candidates:
        return set(), set(), False

    not_authors: set[str] = set()
    authors: set[str] = set()
    applied = {"value": False}

    root = tk.Tk()
    root.title("Вибір авторів")

    root.geometry("900x600")
    root.minsize(700, 420)

    outer = tk.Frame(root, padx=12, pady=10)
    outer.pack(fill="both", expand=True)

    tk.Label(outer, text="Галочка = НЕ автор, без галочки = автор").pack(anchor="w")

    canvas = tk.Canvas(outer, highlightthickness=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview, width=20)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, pady=(6, 0))
    scrollbar.pack(side="right", fill="y", pady=(6, 0))

    items: list[tuple[str, tk.IntVar]] = []
    for idx, name in enumerate(candidates):
        row = idx // 2
        col = idx % 2
        var = tk.IntVar(value=0)
        cb = tk.Checkbutton(scroll_frame, text=name, variable=var)
        cb.grid(row=row, column=col, sticky="w", padx=(0, 18), pady=2)
        items.append((name, var))

    def apply():
        for name, var in items:
            if var.get() == 1:
                not_authors.add(name)
            else:
                authors.add(name)
        applied["value"] = True
        root.destroy()

    btn = tk.Button(outer, text="OK", command=apply)
    btn.pack(anchor="w", pady=(10, 0))

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    return not_authors, authors, applied["value"]


def is_name_with_review(line: str, references: list[str], rejected: set[str], approved: set[str], threshold: float = 0.90) -> bool:
    if not is_name(line):
        return False
    if line in approved:
        return True
    if line in rejected:
        return False
    if not references:
        # no reference list -> accept without review
        return True
    best = 0.0
    for ref in references:
        score = SequenceMatcher(None, line.casefold(), ref.casefold()).ratio()
        if score > best:
            best = score
    if best >= threshold or line in approved:
        return True
    if not INTERACTIVE_REVIEW:
        print(f"[shapka] review: {line} (best={best:.2f})")
        return True
    return False


def collect_review_candidates(
    blocks: list[list[tuple[int, object, str]]],
    references: list[str],
    threshold: float,
    approved: set[str],
    rejected: set[str],
) -> list[str]:
    if not references:
        return []
    ordered: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        for _, _, raw in block:
            line = normalize_line(raw)
            line = fix_title_case(line)
            if is_section_title(line):
                continue
            if not is_name(line):
                continue
            if line in approved or line in rejected:
                continue
            best = 0.0
            for ref in references:
                score = SequenceMatcher(None, line.casefold(), ref.casefold()).ratio()
                if score > best:
                    best = score
            if best < threshold and line not in seen:
                seen.add(line)
                ordered.append(line)
    return ordered


def load_name_db(db_path: Path) -> tuple[set[str], set[str]]:
    if not db_path.exists():
        return set(), set()
    try:
        data = json.loads(db_path.read_text(encoding="utf-8"))
    except Exception:
        return set(), set()
    authors = set(data.get("authors", []) or [])
    not_authors = set(data.get("not_authors", []) or [])
    return authors, not_authors


def load_section_titles(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    titles: set[str] = set()
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            for key in ("section_ua", "section_en"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    titles.add(make_key(val))
    return titles


def _clone_case_rules() -> dict[str, dict[str, dict[str, list[str]]]]:
    return json.loads(json.dumps(DEFAULT_CASE_RULES))


def _normalize_rule_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    result: list[str] = []
    for item in value:
        normalized = str(item).strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _normalize_lang_rules(raw_value) -> dict[str, list[str]]:
    if not isinstance(raw_value, dict):
        return {"phrases": [], "words": []}
    return {
        "phrases": _normalize_rule_list(raw_value.get("phrases")),
        "words": _normalize_rule_list(raw_value.get("words")),
    }


def _merge_flat_rules(target: dict[str, dict[str, list[str]]], raw_value) -> None:
    flat_rules = _normalize_rule_list(raw_value)
    if not flat_rules:
        return
    target["uk"]["phrases"] = list(flat_rules)
    target["uk"]["words"] = []
    target["en"]["phrases"] = []
    target["en"]["words"] = []


def _match_script_groups(line: str) -> list[str]:
    groups: list[str] = []
    if re.search(r"[А-Яа-яІіЇїЄєҐґ]", line):
        groups.append("uk")
    if re.search(r"[A-Za-z]", line):
        groups.append("en")
    if not groups:
        groups.extend(["uk", "en"])
    return groups


def _compile_case_pattern(token: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(token)}(?!\w)", flags=re.IGNORECASE)


def _apply_rule_tokens(line: str, tokens: list[str], transform) -> str:
    changed = line
    for token in sorted(tokens, key=len, reverse=True):
        pattern = _compile_case_pattern(token)
        changed = pattern.sub(lambda _m: transform(token), changed)
    return changed


def apply_case_rules(line: str, rule_type: str) -> str:
    changed = line
    for lang in _match_script_groups(line):
        lang_rules = CASE_RULES.get(rule_type, {}).get(lang, {})
        changed = _apply_rule_tokens(
            changed,
            lang_rules.get("phrases", []),
            lambda token: token if rule_type == "capitalized" else token.lower(),
        )
        changed = _apply_rule_tokens(
            changed,
            lang_rules.get("words", []),
            lambda token: token if rule_type == "capitalized" else token.lower(),
        )
    return changed


def load_case_rules(path: Path) -> dict[str, dict[str, dict[str, list[str]]]]:
    rules = _clone_case_rules()
    if not path.exists():
        return rules
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return rules
    if not isinstance(data, dict):
        return rules

    for config_key, rule_type in (
        ("titlecase_force_capitalized", "capitalized"),
        ("titlecase_force_lowercase", "lowercase"),
    ):
        raw_rules = data.get(config_key)
        if isinstance(raw_rules, list):
            _merge_flat_rules(rules[rule_type], raw_rules)
            continue
        if not isinstance(raw_rules, dict):
            continue
        for lang in ("uk", "en"):
            if lang not in raw_rules:
                continue
            normalized_lang_rules = _normalize_lang_rules(raw_rules.get(lang))
            if normalized_lang_rules["phrases"] or normalized_lang_rules["words"]:
                rules[rule_type][lang] = normalized_lang_rules

    return rules


def save_name_db(db_path: Path, authors: set[str], not_authors: set[str]) -> None:
    data = {
        "authors": sorted(authors),
        "not_authors": sorted(not_authors),
    }
    db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_author_references(run_dir: Path) -> list[str]:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        return []
    try:
        data = json.loads(matches_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    refs: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        authors = item.get("authors")
        if isinstance(authors, list):
            for a in authors:
                if isinstance(a, str) and a.strip():
                    refs.append(a.strip())
    return refs


def apply_style(paragraph, style_name: str) -> None:
    try:
        paragraph.Range.Style = style_name
    except Exception:
        pass


def get_paragraph_text(paragraph) -> str:
    text = paragraph.Range.Text or ""
    return text.rstrip("\r")


def set_paragraph_text(paragraph, text: str) -> None:
    try:
        rng = paragraph.Range
        rng.End -= 1  # keep paragraph mark
        rng.Text = text
    except Exception:
        pass


def ensure_blank_after(paragraph) -> None:
    try:
        after_text = paragraph.Next().Range.Text if paragraph.Next() is not None else ""
        if after_text.strip():
            paragraph.Range.InsertParagraphAfter()
    except Exception:
        pass


def ensure_udc_at_start(doc) -> None:
    # If no UDC/UDK marker on the first page, insert placeholder at document start.
    try:
        total = int(doc.Paragraphs.Count)
    except Exception:
        return
    found = False
    current_page = None
    paras_on_page = 0
    for i in range(1, total + 1):
        para = doc.Paragraphs(i)
        try:
            page_num = int(para.Range.Information(constants.wdActiveEndPageNumber))
        except Exception:
            page_num = None
        if current_page is None or (page_num is not None and page_num != current_page):
            current_page = page_num
            paras_on_page = 0
        paras_on_page += 1
        if current_page is not None and current_page > 1:
            break
        if paras_on_page > PAGE_SCAN_LIMIT:
            break
        try:
            text = (para.Range.Text or "").strip()
        except Exception:
            continue
        if is_udc_like(text):
            found = True
            break
    if found:
        return
    try:
        rng = doc.Range(0, 0)
        rng.InsertBefore("UDC \r")
        first_para = doc.Paragraphs(1)
        apply_style(first_para, "UDC")
        ensure_blank_after(first_para)
    except Exception:
        return


def apply_section_styles(doc) -> None:
    try:
        total = int(doc.Paragraphs.Count)
    except Exception:
        return
    for i in range(1, total + 1):
        para = doc.Paragraphs(i)
        text = (para.Range.Text or "").strip()
        if not text:
            continue
        if not is_section_title(text):
            continue
        # Force section style for known section headings (including long EN captions).
        try:
            apply_style(para, "SECTION")
        except Exception:
            try:
                apply_style(para, "Heading 1")
            except Exception:
                pass


def process_block(
    block_items: list[tuple[int, object, str]],
    references: list[str],
    rejected: set[str],
    approved: set[str],
    threshold: float,
) -> dict:
    # normalize lines and apply to paragraphs
    lines: list[str] = []
    lines_info: list[tuple[object, str, bool]] = []
    for _, para, raw in block_items:
        if EMAIL_RE.search(raw or ""):
            set_paragraph_text(para, "")
            continue
        if is_section_title(raw):
            continue
        if is_udc_like(raw) and not is_section_style(para):
            clean_udc = normalize_udc_line(raw)
            if clean_udc != raw:
                set_paragraph_text(para, clean_udc)
            apply_style(para, "UDC")
            lines.append(clean_udc)
            lines_info.append((para, clean_udc, True))
            continue
        clean_base = normalize_line(raw)
        name_candidate = normalize_name_line(raw)
        if is_name(name_candidate):
            clean = fix_title_case(name_candidate)
        else:
            clean = fix_title_case(strip_non_author_prefix(clean_base))
        if is_section_title(clean):
            continue
        if clean != raw:
            set_paragraph_text(para, clean)
        lines.append(clean)
        lines_info.append((para, clean, False))

    # extract UDC
    udc = next((l for l in lines if is_udc_like(l)), None)
    content_lines: list[str] = []
    content_paras: list[object] = []
    for para, clean, is_udc in lines_info:
        if is_udc:
            continue
        content_lines.append(clean)
        content_paras.append(para)

    # name indices
    name_idx = []
    for i, line in enumerate(content_lines):
        if is_section_title(line):
            continue
        if is_name_with_review(line, references, rejected, approved, threshold=threshold):
            name_idx.append(i)
    if not name_idx:
        return {"udc": udc, "authors": [], "not_authors": [l for l in content_lines if l], "raw_block": lines}

    authors_blocks: list[list[str]] = []
    for i, idx in enumerate(name_idx):
        start = idx
        end = name_idx[i + 1] if i + 1 < len(name_idx) else len(content_lines)
        authors_blocks.append(content_lines[start:end])

    authors = []
    for block in authors_blocks:
        name = block[0]
        authors.append(name)

    # apply styles per paragraph in block
    author_names = set(authors)
    author_idx_set = set(name_idx)
    para_to_idx = {id(p): i for i, p in enumerate(content_paras)}
    for _, para, raw in block_items:
        if is_section_style(para):
            continue
        line = get_paragraph_text(para).strip()
        name_candidate = normalize_name_line(line) if line else ""
        if name_candidate and is_name(name_candidate):
            clean_line = fix_title_case(name_candidate)
        else:
            clean_line = normalize_line(line) if line else ""
            clean_line = strip_non_author_prefix(clean_line)
            clean_line = fix_title_case(clean_line)
        if clean_line != line and clean_line:
            print(f"[shapka] title fix: {line} -> {clean_line}")
        if clean_line != line:
            set_paragraph_text(para, clean_line)
        para_idx = para_to_idx.get(id(para))
        if is_section_title(clean_line):
            continue
        if para_idx is not None and para_idx in author_idx_set and clean_line in author_names:
            rng = para.Range
            rng.End -= 1  # keep paragraph mark
            rng.Text = clean_line
            try:
                rng.Font.AllCaps = True
            except Exception:
                pass
            apply_style(para, "AUTOR")
        elif clean_line and not is_udc_like(clean_line):
            apply_style(para, "pip")

    not_authors = [l for i, l in enumerate(content_lines) if l and i not in name_idx]
    return {"udc": udc, "authors": authors, "not_authors": not_authors, "raw_block": lines}


def collect_blocks(doc) -> list[list[tuple[int, object, str]]]:
    total = int(doc.Paragraphs.Count)
    blocks: list[list[tuple[int, object, str]]] = []
    current: list[tuple[int, object, str]] = []
    current_page = None
    paras_on_page = 0

    for i in range(1, total + 1):
        para = doc.Paragraphs(i)
        try:
            raw_full = para.Range.Text or ""
        except Exception:
            continue
        try:
            page_num = int(para.Range.Information(constants.wdActiveEndPageNumber))
        except Exception:
            page_num = None
        if current_page is None or (page_num is not None and page_num != current_page):
            current_page = page_num
            paras_on_page = 0
        paras_on_page += 1
        if paras_on_page > PAGE_SCAN_LIMIT:
            if len(current) > 2:
                blocks.append(current)
            current = []
            if i % 50 == 0 or i == total:
                print(f"[shapka] {i}/{total}")
            continue

        raw = raw_full.strip()
        if raw in {"\x01", "\x02", "\x03"}:
            raw = ""
        if is_section_title(raw):
            if len(current) > 2:
                blocks.append(current)
            current = []
            if i % 50 == 0 or i == total:
                print(f"[shapka] {i}/{total}")
            continue
        if is_section_style(para):
            if len(current) > 2:
                blocks.append(current)
            current = []
            continue
        if is_title_style(para):
            if len(current) > 2:
                blocks.append(current)
            current = []
            continue
        if not raw:
            if len(current) > 2:
                blocks.append(current)
            current = []
            if i % 50 == 0 or i == total:
                print(f"[shapka] {i}/{total}")
            continue
        if is_udc_like(raw) and not is_body(para):
            current.append((i, para, raw))
        elif is_narrow(para) and not is_body(para) and is_left_block(para):
            current.append((i, para, raw))
        else:
            if len(current) > 2:
                blocks.append(current)
            current = []
        if i % 50 == 0 or i == total:
            print(f"[shapka] {i}/{total}")
    if current:
        blocks.append(current)
    return blocks


def finalize_output(results: list[dict]) -> dict:
    all_authors = []
    all_not_authors = []
    for item in results:
        all_authors.extend(item.get("authors", []))
        all_not_authors.extend(item.get("not_authors", []))

    def uniq_keep_order(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for it in items:
            if it in seen:
                continue
            seen.add(it)
            out.append(it)
        return out

    return {
        "authors": uniq_keep_order(all_authors),
        "not_authors": uniq_keep_order(all_not_authors),
    }


def process_document(
    draft_path: Path,
    references: list[str],
    approved: set[str],
    rejected: set[str],
    threshold: float,
    word,
    progress: tuple[int, int] | None = None,
) -> dict:
    results = []
    doc = None
    try:
        if progress is not None:
            print(f"[shapka] file {progress[0]}/{progress[1]}")
        print(f"[shapka] старт: {draft_path}")
        doc = open_document(word, str(draft_path), read_only=False)

        apply_section_styles(doc)
        ensure_udc_at_start(doc)
        blocks = collect_blocks(doc)
        print(f"[shapka] блоків знайдено: {len(blocks)}")

        candidates = collect_review_candidates(blocks, references, threshold=threshold, approved=approved, rejected=rejected)
        if candidates:
            new_rejected, new_approved, applied = ask_confirm_batch(candidates)
            if applied:
                rejected.update(new_rejected)
                approved.update(new_approved)
                save_name_db(ROOT_DIR / "shapka_core" / "NameNoName.json", approved, rejected)
        for block in blocks:
            lines = [item[2] for item in block]
            if not looks_like_header(lines):
                continue
            result = process_block(block, references, rejected, approved, threshold=threshold)
            results.append(result)
            if result.get("authors"):
                joined = "; ".join(result["authors"])
                print(f"[shapka] authors: {joined}")

        try:
            doc.Save()
        except Exception:
            pass
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass

    output = finalize_output(results)
    print(f"[shapka] готово: {len(results)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse header blocks in draft_journal.docx")
    parser.add_argument("draft", type=Path, help="Path to draft_journal.docx or directory with docx files")
    parser.add_argument("--output-json", type=Path, default=None, help="Output JSON path (file or directory)")
    parser.add_argument("--threshold", type=float, default=0.90, help="Name similarity threshold")
    parser.add_argument("--interactive", action="store_true", help="Показати підтвердження сумнівних ПІБ")
    args = parser.parse_args()

    draft_path = args.draft.resolve()
    if not draft_path.exists():
        raise SystemExit(f"Draft not found: {draft_path}")

    db_path = ROOT_DIR / "shapka_core" / "NameNoName.json"
    run_dir = draft_path if draft_path.is_dir() else draft_path.parent
    references = collect_author_references(run_dir)
    approved, rejected = load_name_db(db_path)
    global SECTION_TITLES, INTERACTIVE_REVIEW, CASE_RULES
    SECTION_TITLES = load_section_titles(ROOT_DIR / "resources" / "name_sektsii.json")
    CASE_RULES = load_case_rules(MARKERS_PATH)
    INTERACTIVE_REVIEW = bool(args.interactive)

    pythoncom.CoInitialize()
    word = None
    try:
        word = start_word_app(log_callback=print)

        if draft_path.is_dir():
            files = [p for p in draft_path.rglob("*.docx") if not p.name.startswith("~$")]
            if not files:
                raise SystemExit(f"No .docx files found in: {draft_path}")
            if args.output_json is None:
                summary_path = draft_path / "shapka_report.json"
            else:
                output_json = args.output_json.resolve()
                if output_json.is_dir():
                    summary_path = output_json / "shapka_report.json"
                else:
                    summary_path = output_json

            summary = []
            files_with_authors = 0
            files_without_authors: list[str] = []
            total_files = len(files)
            for idx, file_path in enumerate(files, start=1):
                try:
                    result = process_document(
                        file_path,
                        references,
                        approved,
                        rejected,
                        args.threshold,
                        word,
                        progress=(idx, total_files),
                    )
                    summary.append({"source": str(file_path), "authors": result["authors"], "not_authors": result["not_authors"]})
                    if result.get("authors"):
                        files_with_authors += 1
                    else:
                        files_without_authors.append(file_path.name)
                except Exception as error:
                    print(f"[shapka] помилка: {file_path} -> {error}")
                    try:
                        shutdown_word_app(word)
                    except Exception:
                        pass
                    word = start_word_app(log_callback=print)
                    continue
            summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[shapka] summary JSON: {summary_path}")
            if total_files:
                percent = (files_with_authors / total_files) * 100.0
                print(f"[shapka] coverage: {files_with_authors}/{total_files} ({percent:.1f}%)")
                if files_without_authors:
                    print("[shapka] без авторів: " + ", ".join(files_without_authors))
        else:
            output_json = args.output_json or draft_path.with_name("shapka_report.json")
            result = process_document(draft_path, references, approved, rejected, args.threshold, word)
            output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[shapka] JSON: {output_json}")
            print(f"[shapka] coverage: {1 if result.get('authors') else 0}/1 ({100.0 if result.get('authors') else 0.0:.1f}%)")
    finally:
        if word is not None:
            try:
                shutdown_word_app(word)
            except Exception:
                pass
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
