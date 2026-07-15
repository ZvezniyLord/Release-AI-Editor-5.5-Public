import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SHARED_DIR = Path(__file__).resolve().parents[1] / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from safe_shutdown import safe_shutdown
from process_cleanup import install_cleanup_hooks
from run_logger import make_logger
from core.dashboard_update import update_dashboard_from_run


def _safe_name(name: str) -> str:
    return "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "article"

def _fix_folder_name(name: str) -> str:
    if name == "Статті":
        return "Статті"
    return name


def relocate_articles(run_dir: Path, target_folder_name: str = "Статті", log_callback=None) -> Path:
    target_folder_name = _fix_folder_name(target_folder_name)
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        raise FileNotFoundError(f"Не знайдено {matches_path}")

    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    # If a mojibake folder already exists, rename it to the correct name.
    bad_dir = run_dir / "Статті"
    target_dir = run_dir / target_folder_name
    try:
        if bad_dir.exists() and not target_dir.exists():
            bad_dir.rename(target_dir)
    except Exception:
        pass
    target_dir.mkdir(parents=True, exist_ok=True)

    name_counts: dict[str, int] = {}
    relocated = []

    total = len(matches)
    for idx, match in enumerate(matches, start=1):
        if log_callback:
            log_callback(f"[relocate] {idx}/{total}")
        if match.get("match_method") in {"missing", "missing_source_file", "free_listener"}:
            continue
        source = Path(match.get("working_path") or match.get("matched_path") or "")
        if not source.exists():
            continue
        matched_source = Path(match.get("matched_path") or "")
        source_name_for_folder = matched_source if matched_source.exists() else source
        base_name = _safe_name(source_name_for_folder.parent.name)
        ext = source.suffix or ".docx"
        count = name_counts.get(base_name, 0) + 1
        name_counts[base_name] = count
        if count > 1:
            dest_name = f"{base_name}_{count}{ext}"
        else:
            dest_name = f"{base_name}{ext}"
        dest = target_dir / dest_name
        shutil.copy2(source, dest)
        match["relocated_path"] = str(dest)
        relocated.append({"from": str(source), "to": str(dest)})

    matches_path.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "relocated_paths.json").write_text(json.dumps(relocated, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_dir


def main() -> None:
    install_cleanup_hooks(log_callback=print)
    parser = argparse.ArgumentParser(description="Ядро перенесення: копіює знайдені статті у папку 'Статті'")
    parser.add_argument("run_dir", type=Path, help="Папка run, де лежить matches.json")
    parser.add_argument("--folder", default="Статті", help="Назва папки для статей")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    logger = make_logger(run_dir, name="relocate_core")
    logger.info("start", run_dir=str(run_dir))

    try:
        target = relocate_articles(run_dir, args.folder, log_callback=print)
        update_stats = update_dashboard_from_run(run_dir, update_relocated=True, update_cleaned=False)
        print(f"Готово. Статті скопійовано у: {target}")
        logger.info("done", target=str(target))
    finally:
        safe_shutdown(log_callback=print)


if __name__ == "__main__":
    main()
