from __future__ import annotations

import json
import sys
from pathlib import Path
import importlib.util

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "scripts" / "run_silver_quality_checkpoint.py"
SPEC = importlib.util.spec_from_file_location("ge_runner_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
ge_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ge_runner)


def test_runner_skips_when_data_missing_and_flag_enabled(tmp_path, monkeypatch):
    output = tmp_path / "ge_report.json"

    def _raise_missing(*args, **kwargs):
        raise FileNotFoundError("Missing data folder: data/bronze/churn")

    monkeypatch.setattr(ge_runner, "run_silver_ge_checkpoint", _raise_missing)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_silver_quality_checkpoint.py",
            "--allow-missing-data",
            "--output",
            str(output),
        ],
    )

    ge_runner.main()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert payload["skipped"] is True
