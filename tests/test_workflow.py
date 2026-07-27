from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([PYTHON, *args], cwd=ROOT, env=ENV, text=True, capture_output=True, check=check)


class WorkflowTests(unittest.TestCase):
    def initialize_locked_run(self) -> Path:
        run_dir = Path(tempfile.mkdtemp(prefix="esa-test-"))
        run("scripts/initialize_run.py", "--project", "assets/example-project.json", "--out", str(run_dir))
        run("scripts/lock_baseline_result.py", "--run-dir", str(run_dir), "--entry", "tests/fixtures/baseline-result.json")
        run("scripts/append_adjustment_log.py", "--log", str(run_dir / "adjustment_log.jsonl"), "--entry", "tests/fixtures/baseline-result.json")
        return run_dir

    def test_full_workflow_and_template_report(self) -> None:
        run_dir = self.initialize_locked_run()
        run("scripts/append_adjustment_log.py", "--log", str(run_dir / "adjustment_log.jsonl"), "--entry", "tests/fixtures/approved-result.json")
        run("scripts/append_audit_event.py", "--run-dir", str(run_dir), "--event", "tests/fixtures/rejected-attempt.json")
        run("scripts/verify_run_integrity.py", "--run-dir", str(run_dir))
        report = run_dir / "report.md"
        run("scripts/summarize_run.py", "--project", str(run_dir / "project.json"), "--log", str(run_dir / "adjustment_log.jsonl"), "--out", str(report))
        rendered = report.read_text(encoding="utf-8")
        for section in range(1, 11):
            self.assertIn(f"## {section}.", rendered)
        self.assertIn("rejected-001", rendered)

    def test_rejects_invalid_numeric_result(self) -> None:
        run_dir = self.initialize_locked_run()
        entry = json.loads((ROOT / "tests/fixtures/approved-result.json").read_text(encoding="utf-8"))
        entry["run_id"] = "bad-numeric"
        entry["result"]["p_value"] = -0.1
        path = run_dir / "bad-entry.json"
        path.write_text(json.dumps(entry), encoding="utf-8")
        result = run("scripts/append_adjustment_log.py", "--log", str(run_dir / "adjustment_log.jsonl"), "--entry", str(path), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("p_value", result.stderr)

    def test_initialize_rejects_invalid_project_period(self) -> None:
        project = json.loads((ROOT / "assets/example-project.json").read_text(encoding="utf-8"))
        project["sample_period"] = {"start": 2025, "end": 2024}
        with tempfile.TemporaryDirectory(prefix="esa-invalid-") as tmp:
            path = Path(tmp) / "project.json"
            path.write_text(json.dumps(project), encoding="utf-8")
            result = run("scripts/initialize_run.py", "--project", str(path), "--out", str(Path(tmp) / "run"), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sample_period.start", result.stderr)

    def test_detects_tampered_log(self) -> None:
        run_dir = self.initialize_locked_run()
        log_path = run_dir / "adjustment_log.jsonl"
        log_path.write_text(log_path.read_text(encoding="utf-8").replace("0.12", "0.13", 1), encoding="utf-8")
        result = run("scripts/verify_run_integrity.py", "--run-dir", str(run_dir), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("entry_sha256", result.stderr)

    def test_rejects_audit_event_before_baseline(self) -> None:
        run_dir = Path(tempfile.mkdtemp(prefix="esa-unlocked-"))
        run("scripts/initialize_run.py", "--project", "assets/example-project.json", "--out", str(run_dir))
        result = run("scripts/append_audit_event.py", "--run-dir", str(run_dir), "--event", "tests/fixtures/rejected-attempt.json", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline尚未锁定", result.stderr)


if __name__ == "__main__":
    unittest.main()
