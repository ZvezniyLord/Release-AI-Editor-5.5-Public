from __future__ import annotations

from pathlib import Path

WORD_SAVE_AS_DOCX = 16
WORD_PAGE_BREAK = 7
WORD_COLLAPSE_END = 0

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
RESOURCES_DIR = PROJECT_DIR / "resources"
DEFAULT_TEMPLATE_PATH = PROJECT_DIR / "assets" / "templates" / "Jurnal.dotx"
DEFAULT_STYLE_REGISTRY_PATH = RESOURCES_DIR / "style_registry.json"
