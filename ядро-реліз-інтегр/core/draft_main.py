import argparse
import sys
import time
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from core.relocate_articles import relocate_articles
from core.build_draft import build_draft


SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
from safe_shutdown import safe_shutdown
from process_cleanup import install_cleanup_hooks
from word_com import warmup_word
from template_resolver import resolve_template_path
from run_logger import make_logger


def main() -> None:
    install_cleanup_hooks(log_callback=print)
    parser = argparse.ArgumentParser(description="Чернетка: перенесення статей і формування draft з папки run")
    parser.add_argument("run_dir", type=Path, nargs="?", default=None, help="Папка run, створена ядром дашборда")
    parser.add_argument("--template", type=Path, default=None, help="Шлях до шаблону Word")
    parser.add_argument("--output", type=Path, default=None, help="Шлях до вихідної чернетки")
    parser.add_argument("--folder", default="Статті", help="Назва папки для статей")
    parser.add_argument("--skip-relocate", action="store_true", help="Пропустити копіювання статей")
    parser.add_argument("--skip-draft", action="store_true", help="Пропустити створення чернетки")
    parser.add_argument("--source-folder", type=Path, default=None, help="Звідки брати статті для чернетки")
    args = parser.parse_args()

    if args.run_dir is None:
        raw = input("Вкажи шлях до run-папки: ").strip()
        if not raw:
            raise SystemExit("Порожній шлях.")
        candidates = []
        if '"' in raw:
            parts = [part for part in raw.split('"') if part.strip()]
            candidates.extend(parts)
        candidates.append(raw)
        run_dir = None
        for cand in candidates:
            path = Path(cand.strip()).resolve()
            if (path / "matches.json").exists():
                run_dir = path
                break
        if run_dir is None:
            raise SystemExit(
                "Не знайдено matches.json у введеному шляху. "
                "Введи шлях до run-папки, наприклад: "
                r"<RUN_OUTPUT_DIR>\zhurnal_YYYYMMDD_HHMMSS"
            )
    else:
        run_dir = args.run_dir.resolve()

    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        raise SystemExit(f"Не знайдено matches.json у {run_dir}. Перевір шлях до run-папки.")
    if not run_dir.exists():
        raise FileNotFoundError(f"Папка не знайдена: {run_dir}")

    logger = make_logger(run_dir, name="draft_core")
    logger.info("start", run_dir=str(run_dir))

    if not args.skip_relocate:
        relocate_articles(run_dir, args.folder)
        logger.info("relocate_done", folder=args.folder)

    try:
        print("[wordcom] ініціалізація Word COM...")
        # Використовуємо один екземпляр Word COM, щоб уникнути повторного запуску.
        # Після cleanup_runtime даємо системі трохи часу завершити COM-процеси.
        time.sleep(1.5)
        word_app = warmup_word(template_path=str(resolve_template_path() or ""), log_callback=print, keep_open=True)
        print("[wordcom] Word COM готовий, стартує збірка чернетки...")
        if not args.skip_draft:
            try:
                print("[draft] збірка чернетки: початок")
                output_path = build_draft(
                    run_dir,
                    args.template,
                    args.output,
                    source_folder=args.source_folder,
                    log_callback=print,
                    word_app=word_app,
                )
                print(f"Чернетку створено: {output_path}")
                logger.info("draft_done", output=str(output_path))
            except RuntimeError as error:
                print(f"Помилка створення чернетки: {error}")
                print("Статті вже скопійовано у папку 'Статті'. Чернетку можна створити пізніше.")
                logger.info("draft_error", error=str(error))
    finally:
        safe_shutdown(log_callback=print)


if __name__ == "__main__":
    main()
