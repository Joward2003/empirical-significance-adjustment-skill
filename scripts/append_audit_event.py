#!/usr/bin/env python3
"""Record a rejected or failed attempt inside an initialized, baseline-locked run."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from audit_utils import (
    ROOT,
    chained_entry_hash,
    load_json,
    load_project,
    read_jsonl,
    registry_index,
    sha256_file,
    validate_audit_event,
    verify_chain,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="记录未批准或失败的规格尝试，不把它当作批准结果。")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--registry", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    snapshot_path = run_dir / "baseline_snapshot.json"
    project_path = run_dir / "project.json"
    log_path = run_dir / "audit_events.jsonl"
    if not snapshot_path.exists() or not project_path.exists():
        raise SystemExit("未找到已初始化运行目录；请先运行initialize_run.py。")
    project = load_project(project_path)
    snapshot = load_json(snapshot_path, "baseline snapshot")
    if snapshot.get("locked") is not True:
        raise SystemExit("baseline尚未锁定；审计事件必须绑定已锁定的基准。")
    project_sha256 = sha256_file(project_path)
    if snapshot.get("project_sha256") != project_sha256:
        raise SystemExit("project.json与baseline_snapshot哈希不一致。")

    registry_path = Path(args.registry) if args.registry else ROOT / "references" / "method-registry.json"
    if snapshot.get("registry_sha256") != sha256_file(registry_path):
        raise SystemExit("方法注册表与baseline_snapshot哈希不一致；请在新运行目录中使用新的注册表。")
    registry = registry_index(registry_path)
    event = load_json(Path(args.event), "审计事件")
    event.setdefault("project_id", project["project_id"])
    event.setdefault("project_sha256", project_sha256)
    event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    validate_audit_event(event, project, project_sha256, registry)

    rows = read_jsonl(log_path)
    verify_chain(rows, "audit_events.jsonl")
    if event["event_id"] in {row.get("event_id") for row in rows}:
        raise SystemExit(f"event_id已存在，拒绝覆盖审计记录: {event['event_id']}")
    event["previous_entry_sha256"] = rows[-1].get("entry_sha256") if rows else None
    event["entry_sha256"] = chained_entry_hash(event)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "audit_event_appended", "event_id": event["event_id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
