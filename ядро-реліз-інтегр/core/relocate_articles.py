import argparse
import json
import shutil
from pathlib import Path


def _safe_name(name: str) -> str:
    return "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip() or "article"


def relocate_articles(run_dir: Path, target_folder_name: str = "Статті") -> Path:
    matches_path = run_dir / "matches.json"
    if not matches_path.exists():
        raise FileNotFoundError(f"Не знайдено {matches_path}")

    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    target_dir = run_dir / target_folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    name_counts: dict[str, int] = {}
    relocated = []

    total = len(matches)
    for idx, match in enumerate(matches, start=1):
        print(f"[relocate] {idx}/{total}")
        if match.get("match_method") in {"missing", "missing_source_file", "free_listener"}:
            continue
        source = Path(match.get("working_path") or match.get("matched_path") or "")
        if not source.exists():
            continue
        base_name = _safe_name(source.parent.name)
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
    parser = argparse.ArgumentParser(description="Копіює знайдені статті у папку 'Статті' та оновлює matches.json")
    parser.add_argument("run_dir", type=Path, help="Папка run, де лежить matches.json")
    parser.add_argument("--folder", default="Статті", help="Назва папки для статей")
    args = parser.parse_args()

    target = relocate_articles(args.run_dir, args.folder)
    print(f"Готово. Статті скопійовано у: {target}")


if __name__ == "__main__":
    main()
