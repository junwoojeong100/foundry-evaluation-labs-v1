"""Build a deterministic source bundle without environments, secrets or run data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    "README.md", "README.en.md", "index.html", "facilitator.html", "admin.html", "sft.html",
    "migration.html", "english.html",
    "verification.html", "data-guide.html", "print.html", "pyproject.toml", "requirements.lock",
    "requirements-verification.lock",
    ".env.example", ".gitignore", ".nojekyll", "Foundry-Learning-Loop-Lab-KO.pdf",
)
SOURCE_DIRS = ("guide", "web", "lab", "scripts", "tests", "data", "prompts", "config", "schemas", "worksheets", "infra", "evidence")
ARCHIVE_ROOT = "foundry-evaluation-labs-v1.1"
FIXED_TIME = (2026, 9, 30, 12, 0, 0)


def package_files(root: Path) -> list[Path]:
    files = [root / name for name in ROOT_FILES if (root / name).is_file()]
    for name in SOURCE_DIRS:
        directory = root / name
        if directory.is_dir():
            for path in directory.rglob("*"):
                if (
                    path.is_file()
                    and not path.is_symlink()
                    and "__pycache__" not in path.parts
                    and path.suffix not in {".pyc", ".pyo"}
                    and not any(part.startswith(".") for part in path.relative_to(root).parts)
                ):
                    files.append(path)
    return sorted(set(files), key=lambda path: path.relative_to(root).as_posix())


def build_archive(root: Path, destination: Path) -> dict:
    files = package_files(root)
    required = (
        "README.md", "index.html", "facilitator.html", "admin.html", "sft.html",
        "verification.html", "data-guide.html", "print.html",
        ".env.example", "requirements.lock", "guide/handbook.md",
    )
    missing = [name for name in required if root / name not in files]
    if missing:
        raise ValueError("Required deliverables are missing: " + ", ".join(missing))
    manifest = {
        "version": "1.1.0",
        "guide_checked_date": "2026-09-30",
        "excluded": [".env", ".venv", ".lab", "artifacts", "credentials", "raw live evaluation/training results"],
        "included_evidence": "Only sanitized, allowlisted evidence/ summaries and documentation screenshots.",
        "files": {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            entry = ZipInfo(f"{ARCHIVE_ROOT}/{path.relative_to(root).as_posix()}", date_time=FIXED_TIME)
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
        entry = ZipInfo(f"{ARCHIVE_ROOT}/PACKAGE-MANIFEST.json", date_time=FIXED_TIME)
        entry.compress_type = ZIP_DEFLATED
        archive.writestr(entry, json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist/foundry-evaluation-labs-v1.1.zip")
    args = parser.parse_args()
    manifest = build_archive(ROOT, args.out)
    print(f"{args.out}: {len(manifest['files'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
