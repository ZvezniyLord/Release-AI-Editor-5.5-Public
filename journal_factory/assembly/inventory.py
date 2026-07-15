from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InventoryItem:
    relative_path: str
    sha256: str
    size: int


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory_tree(root: Path, suffixes: set[str] | None = None) -> list[InventoryItem]:
    items = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        items.append(
            InventoryItem(
                relative_path=path.relative_to(root).as_posix(),
                sha256=sha256_file(path),
                size=path.stat().st_size,
            )
        )
    return items
