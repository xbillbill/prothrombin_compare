from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data"
OUTPUTS = PROJECT_ROOT / "outputs"
SUMMARY_PATH = OUTPUTS / "run_summary.json"


def ensure_dirs() -> None:
    for path in [
        DATA / "raw",
        DATA / "sequences",
        DATA / "structures",
        DATA / "alignments",
        OUTPUTS / "figures",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def load_summary() -> dict[str, Any]:
    ensure_dirs()
    if SUMMARY_PATH.exists():
        return json.loads(SUMMARY_PATH.read_text())
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "human_accession": "P00734",
        "rabbit_accession": None,
        "rabbit_sequence_status": "unresolved",
        "structure_sources": {},
        "deletion_detected": None,
        "warnings": [],
        "generated_files": [],
    }


def save_summary(summary: dict[str, Any]) -> None:
    ensure_dirs()
    summary["timestamp"] = datetime.now(timezone.utc).isoformat()
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def add_warning(summary: dict[str, Any], message: str) -> None:
    warnings = summary.setdefault("warnings", [])
    if message not in warnings:
        warnings.append(message)


def add_generated(summary: dict[str, Any], path: Path) -> None:
    generated = summary.setdefault("generated_files", [])
    item = rel(path)
    if item not in generated:
        generated.append(item)


def remove_generated(summary: dict[str, Any], path: Path) -> None:
    item = rel(path)
    generated = summary.setdefault("generated_files", [])
    summary["generated_files"] = [existing for existing in generated if existing != item]


def write_text(path: Path, text: str, summary: dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if summary is not None:
        add_generated(summary, path)


def validate_nonempty(path: Path, label: str) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(f"{label} is missing or empty: {path}")
