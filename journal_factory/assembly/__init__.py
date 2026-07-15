"""Raw-source to ETALON assembly helpers.

This package is intentionally fixture-safe: callers provide all paths and
conference variables. No private conference paths, names, titles, or IDs are
embedded here.
"""

from .matcher import ArticleExpectation, CandidateEvidence, MatchDecision, decide_match
from .package_importer import assemble_articles_into_etalon

__all__ = [
    "ArticleExpectation",
    "CandidateEvidence",
    "MatchDecision",
    "assemble_articles_into_etalon",
    "decide_match",
]
