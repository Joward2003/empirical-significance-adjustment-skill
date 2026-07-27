#!/usr/bin/env python3
"""Verify structural integrity, schemas, registry bindings, and hash chains for one run."""
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
    validate_audit_event,
    verify_chain,
)


def verify_run_dir(run_dir: Path, registry_path: Path | None = None) -> tuple[dict, dict, list[dict], list[dict]]:
    snapshot_path = run_dir / "baseline_snapshot.json"
    project_path = run_dir / "project.json"
    log_path = run_dir / "adjustment_log.jsonl"
    event_path = run_dir / "audit_events.jsonl"
    for path in (snapshot_path, project_path, log_path, event_path):
        if not path.exists():
            raise SystemExit(f"运行目录缺少审计文件: {path.name}")

    project = load_project(project_path)
    snapshot = load_json(snapshot_path, "baseline snapshot")
    project_sha256 = sha256_file(project_path)
    active_registry_path = registry_path or ROOT / "references" / "method-registry.json"
    if snapshot.get("locked") is not True or not snapshot.get("baseline_entry_sha256"):
        raise SystemExit("baseline_snapshot尚未锁定完整基准结果")
    if snapshot.get("project_sha256") != project_sha256:
        raise SystemExit("project.json与baseline_snapshot的哈希不一致")
    if snapshot.get("registry_sha256") != sha256_file(active_registry_path):
        raise SystemExit("方法注册表与baseline_snapshot哈希不一致；请在新运行目录中使用新的注册表。")

    registry = registry_index(active_registry_path)
    entries = read_jsonl(log_path)
    events = read_jsonl(event_path)
    verify_chain(entries, "adjustment_log.jsonl")
    verify_chain(events, "audit_events.jsonl")
    if not entries or not entries[0].get("method_id", "").startswith("baseline_"):
        raise SystemExit("调整日志第一条必须是基准记录")
    if sum(entry.get("method_id", "").startswith("baseline_") for entry in entries) != 1:
        raise SystemExit("调整日志必须恰有一条基准记录")
    for entry in entries:
        validate_approved_entry({k: v for k, v in entry.items() if k not in {"previous_entry_sha256", "entry_sha256"}}, registry)
    for event in events:
        validate_audit_event({k: v for k, v in event.items() if k not in {"previous_entry_sha256", "entry_sha256"}}, project, project_sha256, registry)

    baseline = entries[0]
    if baseline.get("run_id") != snapshot.get("baseline_run_id"):
        raise SystemExit("日志基准run_id与snapshot不一致")
    if entry_identity_hash(baseline) != snapshot["baseline_entry_sha256"]:
        raise SystemExit("日志基准记录与snapshot锁定记录不一致")
    if baseline.get("result") != snapshot.get("baseline_result"):
        raise SystemExit("日志基准result与snapshot不一致")
    return project, snapshot, entries, events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--registry", default=None)
    args = parser.parse_args()
    project, _snapshot, entries, events = verify_run_dir(Path(args.run_dir), Path(args.registry) if args.registry else None)
    print(json.dumps({"valid": True, "project_id": project["project_id"], "approved_entries": len(entries), "audit_events": len(events)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
