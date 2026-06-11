from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

CLASSES = ["Blackheads", "Cyst", "Papules", "Pustules", "Whiteheads"]
SPLITS = ["train", "valid", "test"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild archive2 AcneDataset_by_class from split folders.")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(r"D:\의료AI\archive2\AcneDataset"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(r"D:\의료AI\archive2\AcneDataset_by_class"),
    )
    parser.add_argument("--execute", action="store_true", help="Actually rebuild the output folder.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the planned changes.")
    return parser.parse_args()


def collect_plan(source_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for split in SPLITS:
        for cls in CLASSES:
            for src in sorted((source_root / split / cls).glob("*.jpg"), key=lambda p: p.name.lower()):
                rows.append(
                    {
                        "split": split,
                        "class": cls,
                        "source": str(src),
                        "output_name": f"{split}__{src.name}",
                    }
                )
    return rows


def main() -> None:
    args = parse_args()
    if not args.source_root.is_dir():
        raise SystemExit(f"source root not found: {args.source_root}")
    if args.dry_run and args.execute:
        raise SystemExit("choose only one of --dry-run or --execute")

    plan = collect_plan(args.source_root)
    counts: dict[str, int] = {cls: 0 for cls in CLASSES}
    for row in plan:
        counts[row["class"]] += 1

    print(f"source_root={args.source_root}")
    print(f"output_root={args.output_root}")
    print(f"total_images={len(plan)}")
    for cls in CLASSES:
        print(f"{cls}: {counts[cls]}")

    if not args.execute:
        print("dry run only; pass --execute to rebuild")
        return

    if args.output_root.exists():
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True)

    manifest_path = args.output_root / "class_merge_manifest.csv"
    for cls in CLASSES:
        (args.output_root / cls).mkdir(parents=True, exist_ok=True)

    with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["split", "class", "source_rel", "output_rel", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in plan:
            src = Path(row["source"])
            dest = args.output_root / row["class"] / row["output_name"]
            shutil.copy2(src, dest)
            writer.writerow(
                {
                    "split": row["split"],
                    "class": row["class"],
                    "source_rel": str(src.relative_to(args.source_root)).replace("\\", "/"),
                    "output_rel": str(dest.relative_to(args.output_root)).replace("\\", "/"),
                    "status": "copied",
                }
            )
    print("rebuilt output folder")


if __name__ == "__main__":
    main()
