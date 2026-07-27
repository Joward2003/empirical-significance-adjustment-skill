#!/usr/bin/env python3
"""Seal one validated baseline result before any approved adjustment is logged."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_utils import (
    ROOT,
    entry_identity_hash,
    load_json,
    load_project,
    read_jsonl,
    registry_index,
    sha256_file,
    validate_approved_entry,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--entry", required=True, help="JSON baseline log entry")
    parser.add_argument("--registry", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    snapshot_path = run_dir / "baseline_snapshot.json"
    project_path = run_dir / "project.json"
    log_path = run_dir / "adjustment_log.jsonl"
    event_path = run_dir / "audit_events.jsonl"
    if not snapshot_path.exists() or not project_path.exists() or not event_path.exists():
        raise SystemExit("未找到完整运行目录；请先运行initialize_run.py。")
    load_project(project_path)
    snapshot = load_json(snapshot_path, "baseline snapshot")
    if snapshot.get("project_sha256") != sha256_file(project_path):
        raise SystemExit("project.json与baseline_snapshot哈希不一致。")
    if snapshot.get("baseline_result") is not None or snapshot.get("locked") is True:
        raise SystemExit("基准结果已经锁定；拒绝覆盖。请创建新的运行目录。")
    entries = read_jsonl(log_path)
    events = read_jsonl(event_path)
    if entries or events:
        raise SystemExit("基准必须在任何批准运行或审计事件前锁定；请创建新的运行目录。")

    registry_path = Path(args.registry) if args.registry else ROOT / "references" / "method-registry.json"
    if snapshot.get("registry_sha256") != sha256_file(registry_path):
        raise SystemExit("方法注册表与baseline_snapshot哈希不一致；请在新运行目录中使用新的注册表。")
    registry = registry_index(registry_path)
    entry = load_json(Path(args.entry), "基准记录")
    validate_approved_entry(entry, registry)
    if not entry["method_id"].startswith("baseline_"):
        raise SystemExit("entry必须是method_id以baseline_开头的基准模型")
    if entry["status"] in {"failed", "not_run"}:
        raise SystemExit("基准结果必须是一次完成的可估计运行")

    snapshot["baseline_run_id"] = entry["run_id"]
    snapshot["baseline_result"] = entry["result"]
    snapshot["baseline_entry_sha256"] = entry_identity_hash(entry)
    snapshot["locked"] = True
    temp_path = snapshot_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(snapshot_path)
    print(json.dumps({"status": "baseline_locked", "run_id": snapshot["baseline_run_id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
