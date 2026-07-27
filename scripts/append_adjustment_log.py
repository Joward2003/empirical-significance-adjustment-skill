#!/usr/bin/env python3
"""Append a validated, p-value-independent estimation run to a sealed run."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from audit_utils import (
    ROOT,
    chained_entry_hash,
    entry_identity_hash,
    load_json,
    load_project,
    read_jsonl,
    registry_index,
    sha256_file,
    validate_approved_entry,
    verify_chain,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, help="Path to run-output/adjustment_log.jsonl")
    parser.add_argument("--entry", required=True)
    parser.add_argument("--registry", default=None)
    args = parser.parse_args()

    log_path = Path(args.log)
    run_dir = log_path.parent
    snapshot_path = run_dir / "baseline_snapshot.json"
    project_path = run_dir / "project.json"
    if not snapshot_path.exists() or not project_path.exists():
        raise SystemExit("未找到已初始化运行目录；请先运行initialize_run.py。")
    project = load_project(project_path)
    snapshot = load_json(snapshot_path, "baseline snapshot")
    if snapshot.get("locked") is not True:
        raise SystemExit("baseline尚未锁定；不得写入调整日志。")
    if snapshot.get("project_sha256") != sha256_file(project_path):
        raise SystemExit("project.json与baseline_snapshot哈希不一致。")

    registry_path = Path(args.registry) if args.registry else ROOT / "references" / "method-registry.json"
    if snapshot.get("registry_sha256") != sha256_file(registry_path):
        raise SystemExit("方法注册表与baseline_snapshot哈希不一致；请在新运行目录中使用新的注册表。")
    registry = registry_index(registry_path)
    entry = load_json(Path(args.entry), "调整记录")
    entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    validate_approved_entry(entry, registry)

    rows = read_jsonl(log_path)
    verify_chain(rows, "adjustment_log.jsonl")
    if entry["run_id"] in {row.get("run_id") for row in rows}:
        raise SystemExit(f"run_id已存在，拒绝覆盖审计记录: {entry['run_id']}")
    if entry["method_id"].startswith("baseline_"):
        if rows:
            raise SystemExit("基准记录必须是日志第一条；不得追加第二条baseline。")
        if entry["run_id"] != snapshot.get("baseline_run_id") or entry["result"] != snapshot.get("baseline_result"):
            raise SystemExit("基准记录与baseline_snapshot不一致。")
        if entry_identity_hash(entry) != snapshot.get("baseline_entry_sha256"):
            raise SystemExit("基准记录与baseline_snapshot不一致。")
    elif not rows or not rows[0].get("method_id", "").startswith("baseline_"):
        raise SystemExit("必须先把被锁定的baseline记录追加到日志，再追加调整结果。")

    entry["previous_entry_sha256"] = rows[-1].get("entry_sha256") if rows else None
    entry["entry_sha256"] = chained_entry_hash(entry)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "appended", "run_id": entry["run_id"], "level": entry["adjustment_level"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
