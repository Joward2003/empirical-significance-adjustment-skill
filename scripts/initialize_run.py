#!/usr/bin/env python3
"""Create an auditable run directory from a validated project configuration."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from audit_utils import ROOT, load_project, sha256_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source_path = Path(args.project)
    project = load_project(source_path)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    project_path = out / "project.json"
    serialized = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
    if project_path.exists() and project_path.read_text(encoding="utf-8") != serialized:
        raise SystemExit("运行目录已包含不同的project.json；请新建运行目录，避免覆盖审计配置。")
    if not project_path.exists():
        project_path.write_text(serialized, encoding="utf-8")

    snapshot_path = out / "baseline_snapshot.json"
    snapshot_created = not snapshot_path.exists()
    if snapshot_created:
        snapshot = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project_sha256": sha256_file(project_path),
            "registry_sha256": sha256_file(ROOT / "references" / "method-registry.json"),
            "baseline_specification": project["baseline_specification"],
            "baseline_result": None,
            "locked": False,
            "integrity_scope": (
                "Hash chains detect edits made after a run record is created. They are not an external signature "
                "or a guarantee against a party able to rewrite every local file."
            ),
        }
        snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for filename in ("adjustment_log.jsonl", "audit_events.jsonl"):
        (out / filename).touch(exist_ok=True)
    print(json.dumps({"status": "initialized", "out": str(out), "baseline_snapshot_created": snapshot_created}, ensure_ascii=False))


if __name__ == "__main__":
    main()
