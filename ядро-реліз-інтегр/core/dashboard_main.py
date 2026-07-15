import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.dashboard_run import run_dashboard

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
from process_cleanup import install_cleanup_hooks
from run_logger import make_logger


def _configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> None:
    _configure_stdout()
    install_cleanup_hooks(log_callback=print)
    parser = argparse.ArgumentParser(description="Стартовий модуль: готує дашборд і JSON по одній цільовій папці")
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=None,
        help="Шлях до цільової папки, що містить 'учасники' та 'заявки'",
    )
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "output", help="Куди складати run")
    parser.add_argument("--name", default="zhurnal", help="Ім'я вихідного набору (slug для run)")
    parser.add_argument("--threshold", type=float, default=0.80, help="Поріг матчингу назв статей")
    parser.add_argument(
        "--interactive-match",
        action="store_true",
        help="Питати підтвердження для кандидатів з проміжним скором",
    )
    parser.add_argument(
        "--interactive-min-score",
        type=float,
        default=0.10,
        help="Нижня межа для інтерактивних кандидатів (0.1 або 10)",
    )
    parser.add_argument(
        "--interactive-max-score",
        type=float,
        default=0.80,
        help="Верхня межа для інтерактивних кандидатів (0.8 або 80)",
    )
    parser.add_argument(
        "--interactive-add-unknown",
        action="store_true",
        help="Питати про додавання документів, яких немає в Excel",
    )
    parser.add_argument("--preclean", action="store_true", help="Очищати джерела статей перед збіркою")
    parser.add_argument("--stats", action="store_true", help="Додати вкладку статистики без запиту")
    parser.add_argument("--no-stats", action="store_true", help="Не додавати вкладку статистики і не питати")
    parser.add_argument(
        "--convert-mode",
        choices=["auto", "com", "skip"],
        default="auto",
        help="Як працювати з не-docx (.doc/.dot/.rtf/.odt): auto/com = конвертація через Word COM, skip = пропуск",
    )
    args = parser.parse_args()

    logger = make_logger(args.output.resolve() / "logs", name=f"dashboard_{args.name}")
    logger.info("start", target=str(args.target))
    run_dashboard(args)


if __name__ == "__main__":
    main()
