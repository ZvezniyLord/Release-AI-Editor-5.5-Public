"""Docker-first local LLM contracts for Journal Factory.

The package is intentionally separated from journal assembly code.  It only
prepares JSON chunks, calls a provider-neutral local API, and validates model
JSON before deterministic code can consume decisions.
"""

from __future__ import annotations

__all__ = [
    "chunking",
    "client",
    "contracts",
    "host_runner",
    "public_handoff",
    "synthetic",
    "templates",
]
