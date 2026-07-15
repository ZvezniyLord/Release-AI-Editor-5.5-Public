from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArticleExpectation:
    article_id: str
    order: int
    section: str
    authors: list[str]
    title: str
    doi: str | None = None


@dataclass(frozen=True)
class CandidateEvidence:
    candidate_id: str
    source_authors: list[str] = field(default_factory=list)
    source_title: str | None = None
    source_doi: str | None = None
    application_authors: list[str] = field(default_factory=list)
    application_title: str | None = None
    application_doi: str | None = None
    folder_hint: str | None = None
    unused_file_hint: bool = False


@dataclass(frozen=True)
class MatchDecision:
    article_id: str
    candidate_id: str
    status: str
    author_match: bool
    title_match: bool
    doi_match: bool
    semantic_pair: str | None
    confidence: float
    notes: list[str]


TRANSLIT = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "h",
    "\u0491": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0454": "ie",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "y",
    "\u0456": "i",
    "\u0457": "i",
    "\u0439": "i",
    "\u043a": "k",
    "\u043b": "l",
    "\u043c": "m",
    "\u043d": "n",
    "\u043e": "o",
    "\u043f": "p",
    "\u0440": "r",
    "\u0441": "s",
    "\u0442": "t",
    "\u0443": "u",
    "\u0444": "f",
    "\u0445": "kh",
    "\u0446": "ts",
    "\u0447": "ch",
    "\u0448": "sh",
    "\u0449": "shch",
    "\u044c": "",
    "\u044e": "iu",
    "\u044f": "ia",
}


def normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()


def transliterate(text: str) -> str:
    return "".join(TRANSLIT.get(ch.lower(), ch.lower()) for ch in text)


def evidence_tokens(text: str | None) -> set[str]:
    base = normalize_text(text)
    tokens = re.findall(r"[\w']{3,}", base, re.U)
    translit_tokens = re.findall(r"[A-Za-z0-9']{3,}", transliterate(base), re.U)
    return {item.casefold() for item in tokens + translit_tokens}


def semantic_text_match(expected: str | None, observed: str | None, min_ratio: float = 0.82) -> bool:
    expected_norm = normalize_text(expected).casefold()
    observed_norm = normalize_text(observed).casefold()
    if not expected_norm or not observed_norm:
        return False
    if expected_norm == observed_norm or expected_norm in observed_norm or observed_norm in expected_norm:
        return True
    expected_tokens = evidence_tokens(expected_norm)
    observed_tokens = evidence_tokens(observed_norm)
    if not expected_tokens:
        return False
    return len(expected_tokens & observed_tokens) / len(expected_tokens) >= min_ratio


def author_match(expected_authors: list[str], observed_authors: list[str]) -> bool:
    for expected in expected_authors:
        expected_tokens = evidence_tokens(expected)
        if not expected_tokens:
            continue
        for observed in observed_authors:
            observed_tokens = evidence_tokens(observed)
            if expected_tokens and len(expected_tokens & observed_tokens) / len(expected_tokens) >= 0.5:
                return True
    return False


def doi_match(expected: str | None, observed_values: list[str | None]) -> bool:
    expected_norm = normalize_text(expected).casefold()
    if not expected_norm:
        return False
    return any(expected_norm == normalize_text(item).casefold() for item in observed_values if item)


def decide_match(expectation: ArticleExpectation, candidate: CandidateEvidence) -> MatchDecision:
    observed_authors = candidate.source_authors + candidate.application_authors
    author_ok = author_match(expectation.authors, observed_authors)
    title_ok = semantic_text_match(expectation.title, candidate.source_title) or semantic_text_match(
        expectation.title, candidate.application_title
    )
    doi_ok = doi_match(expectation.doi, [candidate.source_doi, candidate.application_doi])

    semantic_pair = None
    if author_ok and title_ok:
        semantic_pair = "author+title"
    elif author_ok and doi_ok:
        semantic_pair = "author+doi"
    elif title_ok and doi_ok:
        semantic_pair = "title+doi"

    notes = []
    if candidate.folder_hint:
        notes.append("folder_hint_recorded_but_not_sufficient")
    if candidate.unused_file_hint:
        notes.append("unused_file_hint_recorded_but_not_sufficient")
    if semantic_pair is None:
        notes.append("requires_two_independent_semantic_evidence_items")

    evidence_count = sum([author_ok, title_ok, doi_ok])
    return MatchDecision(
        article_id=expectation.article_id,
        candidate_id=candidate.candidate_id,
        status="matched" if semantic_pair else "review",
        author_match=author_ok,
        title_match=title_ok,
        doi_match=doi_ok,
        semantic_pair=semantic_pair,
        confidence=evidence_count / 3,
        notes=notes,
    )
