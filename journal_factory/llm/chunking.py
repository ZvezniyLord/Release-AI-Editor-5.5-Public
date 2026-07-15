from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable


class ContextOverflowError(ValueError):
    """Raised when input cannot fit without truncation."""


@dataclass(frozen=True)
class Paragraph:
    paragraph_id: str
    text: str
    context_only: bool = False

    def estimated_tokens(self) -> int:
        # Conservative enough for smoke tests without binding to one tokenizer.
        return max(1, ceil(len(self.text) / 4)) + 6


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    paragraphs: tuple[Paragraph, ...]
    estimated_tokens: int
    rechunked: bool = False

    @property
    def paragraph_ids(self) -> list[str]:
        return [paragraph.paragraph_id for paragraph in self.paragraphs]


def estimate_prompt_tokens(paragraphs: Iterable[Paragraph], prompt_overhead_tokens: int = 512) -> int:
    return prompt_overhead_tokens + sum(paragraph.estimated_tokens() for paragraph in paragraphs)


def chunk_paragraphs(
    paragraphs: Iterable[Paragraph],
    *,
    max_context_tokens: int,
    max_output_tokens: int,
    prompt_overhead_tokens: int = 512,
    overflow_policy: str = "rechunk",
) -> list[Chunk]:
    """Split paragraphs without truncating or reordering IDs."""

    if overflow_policy not in {"rechunk", "fail"}:
        raise ValueError(f"unsupported overflow_policy: {overflow_policy}")
    usable_tokens = max_context_tokens - max_output_tokens - prompt_overhead_tokens
    if usable_tokens <= 0:
        raise ContextOverflowError("max output and prompt overhead exceed context window")

    chunks: list[Chunk] = []
    current: list[Paragraph] = []
    current_tokens = 0
    for paragraph in paragraphs:
        para_tokens = paragraph.estimated_tokens()
        if para_tokens > usable_tokens:
            raise ContextOverflowError(
                f"paragraph {paragraph.paragraph_id} cannot fit without truncation"
            )
        if current and current_tokens + para_tokens > usable_tokens:
            if overflow_policy == "fail":
                raise ContextOverflowError("context overflow and overflow_policy=fail")
            chunks.append(
                Chunk(
                    chunk_id=f"chunk-{len(chunks) + 1:03d}",
                    paragraphs=tuple(current),
                    estimated_tokens=prompt_overhead_tokens + current_tokens,
                    rechunked=True,
                )
            )
            current = []
            current_tokens = 0
        current.append(paragraph)
        current_tokens += para_tokens

    if current:
        chunks.append(
            Chunk(
                chunk_id=f"chunk-{len(chunks) + 1:03d}",
                paragraphs=tuple(current),
                estimated_tokens=prompt_overhead_tokens + current_tokens,
                rechunked=len(chunks) > 0,
            )
        )
    return chunks
