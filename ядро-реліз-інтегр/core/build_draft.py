import argparse
import json
from pathlib import Path

from draft_core.constants import DEFAULT_TEMPLATE_PATH
from draft_core.word_draft_builder import build_draft_with_word


def _resolve_template(template: Path | None) -> Path:
    if template is not None:
        return template
    candidates = [
        DEFAULT_TEMPLATE_PATH,
        Path(__file__).resolve().parents[1] / "assets" / "templates" / "Jurnal.dotx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_draft(
    run_dir: Path,
    template: Path | None = None,
    output: Path | None = None,
    *,
    source_folder: Path | None = None,
    log_callback=None,
    word_app=None,
) -> Path:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        raise FileNotFoundError(f"Не знайдено {matches_path}")
    matches = json.loads(matches_path.read_text(encoding="utf-8"))

    template_path = _resolve_template(template)
    if not template_path.exists():
        value = input("Не знайдено шаблон. Вкажи шлях до Jurnal.dotx: ").strip().strip('"')
        if not value:
            raise FileNotFoundError("Шаблон не знайдено і шлях не вказано.")
        template_path = Path(value).resolve()
    output_path = output or (run_dir / "draft_journal.docx")
    build_draft_with_word(
        template_path,
        output_path,
        matches,
        source_folder=source_folder,
        log_callback=log_callback,
        word_app=word_app,
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Формує чернетку журналу з matches.json")
    parser.add_argument("run_dir", type=Path, help="Папка run, де лежить matches.json")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH, help="Шлях до шаблону Word")
    parser.add_argument("--output", type=Path, default=None, help="Шлях до вихідної чернетки")
    parser.add_argument("--source-folder", type=Path, default=None, help="Звідки брати статті (папка)")
    args = parser.parse_args()

    output_path = build_draft(
        args.run_dir,
        args.template,
        args.output,
        source_folder=args.source_folder,
        log_callback=print,
    )
    print(f"Чернетку створено: {output_path}")


if __name__ == "__main__":
    main()
