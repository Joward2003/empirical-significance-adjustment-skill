#!/usr/bin/env python3
"""Seal the observed baseline result exactly once before adjustments begin."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--entry', required=True, help='JSON baseline log entry')
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    snapshot_path = run_dir / 'baseline_snapshot.json'
    if not snapshot_path.exists():
        raise SystemExit('未找到baseline_snapshot.json；请先运行initialize_run.py')
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    if snapshot.get('baseline_result') is not None:
        raise SystemExit('基准结果已经锁定；拒绝覆盖。请创建新的运行目录。')
    log_path = run_dir / 'adjustment_log.jsonl'
    if log_path.exists() and log_path.read_text(encoding='utf-8').strip():
        raise SystemExit('调整日志已有记录；基准必须在任何调整前锁定。请创建新的运行目录。')

    raw_entry = Path(args.entry).read_bytes()
    entry = json.loads(raw_entry)
    if not str(entry.get('method_id', '')).startswith('baseline_'):
        raise SystemExit('entry必须是method_id以baseline_开头的基准模型')
    if entry.get('decision_used_p_value') is not False:
        raise SystemExit('基准模型的decision_used_p_value必须为false')
    result = entry.get('result')
    required_result = ('beta', 'se', 'p_value', 'ci_low', 'ci_high', 'n', 'clusters')
    if not isinstance(result, dict) or any(result.get(key) is None for key in required_result):
        raise SystemExit('基准结果必须完整包含beta、se、p_value、95%CI、N和clusters')

    snapshot['baseline_run_id'] = entry.get('run_id')
    snapshot['baseline_result'] = result
    snapshot['baseline_entry_sha256'] = hashlib.sha256(raw_entry).hexdigest()
    snapshot['locked'] = True
    temp_path = snapshot_path.with_suffix('.json.tmp')
    temp_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp_path.replace(snapshot_path)
    print(json.dumps({'status': 'baseline_locked', 'run_id': snapshot['baseline_run_id']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
