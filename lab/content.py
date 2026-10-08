"""Select an explicit corpus without changing the original Korean assets."""

import os
from pathlib import Path

from lab.config import LabError, active_config


LANGUAGES = ("ko", "en")


def selected_language() -> str:
    config = active_config()
    value = config.language if config and config.language is not None else os.environ.get("LAB_LANGUAGE", "ko")
    if value not in LANGUAGES:
        raise LabError(f"Unsupported LAB_LANGUAGE={value!r}; choose ko or en before starting the CLI.")
    return value


def content_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise LabError("Content paths must be relative to the lab repository.")
    language = selected_language()
    if language == "en" and path.parts[0] in {"data", "prompts"}:
        return root / path.parts[0] / "en" / Path(*path.parts[1:])
    return root / path


def language_metadata() -> dict:
    # Missing language in older receipts means the original Korean-only corpus.
    return {"language": "en"} if selected_language() == "en" else {}


def require_content_language(record: dict) -> None:
    if not isinstance(record, dict):
        raise LabError("Language provenance must be a JSON object.")
    recorded = record.get("language", "ko")
    if recorded not in LANGUAGES:
        raise LabError(f"Invalid recorded content language: {recorded!r}.")
    if recorded != selected_language():
        raise LabError(
            f"This evidence uses {recorded}; set LAB_LANGUAGE={recorded}. "
            "Do not mix languages or relabel an existing run."
        )


def dataset_files(root: Path) -> list[Path]:
    directory = content_path(root, "data")
    return [
        path for path in sorted(directory.rglob("*.jsonl"))
        if "calibration" not in path.relative_to(directory).parts
        and not (selected_language() == "ko" and path.is_relative_to(root / "data/en"))
    ]


def text(korean: str, english: str, *, language: str | None = None) -> str:
    value = selected_language() if language is None else language
    if value not in LANGUAGES:
        raise LabError(f"Unsupported language={value!r}; choose ko or en.")
    return english if value == "en" else korean
