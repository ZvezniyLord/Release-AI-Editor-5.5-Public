from __future__ import annotations

from pathlib import Path
import json

SUPPORTED_WORD_EXTENSIONS = {".doc", ".docx", ".docm", ".dot", ".dotx", ".dotm", ".rtf", ".odt"}
WORD_SAVE_AS_DOCX = 16
WORD_HEADING_1 = -2
WORD_PAGE_BREAK = 7
WORD_COLLAPSE_END = 0

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
RESOURCES_DIR = PROJECT_DIR / "resources"
DEFAULT_TEMPLATE_PATH = PROJECT_DIR / "assets" / "templates" / "Jurnal.dotx"
DEFAULT_SECTIONS_PATH = RESOURCES_DIR / "name_sektsii.json"
DEFAULT_STYLE_REGISTRY_PATH = RESOURCES_DIR / "style_registry.json"


def _load_marker_list(key: str) -> tuple[str, ...] | None:
    path = RESOURCES_DIR / "markers.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    items = data.get(key)
    if not isinstance(items, list):
        return None
    return tuple(str(x).casefold() for x in items if str(x).strip())

_NON_ARTICLE_MARKERS_DEFAULT = (
    "анкета",
    "заявка",
    "квитан",
    "оплат",
    "receipt",
    "payment",
    "довідка",
    "справка",
    "author info",
    "авторська довідка",
    "відомості про автора",
    "відомості про авторів",
    "інформація про автора",
    "інформація про авторів",
    "transaction",
    "viber",
    "screenshot",
    "screen",
)

_NON_ARTICLE_TEXT_MARKERS_DEFAULT = (
    "анкета-заявка",
    "анкета учасника",
    "квитанція",
    "оплата",
    "довідка",
    "стовпець анкетної форми",
    "інформація для заповнення",
    "ім’я і прізвище автора публікації",
    "author information",
)

NON_ARTICLE_MARKERS = _load_marker_list("non_article_markers") or _NON_ARTICLE_MARKERS_DEFAULT
NON_ARTICLE_TEXT_MARKERS = _load_marker_list("non_article_text_markers") or _NON_ARTICLE_TEXT_MARKERS_DEFAULT
