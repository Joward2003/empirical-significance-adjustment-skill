#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REQ = [
    'run_id', 'method_id', 'adjustment_level', 'rationale',
    'decision_used_p_value', 'specification', 'result', 'status'
]


def registry_index(path: Path) -> dict:
    try:
        registry = json.loads(path.read_text(encoding='utf-8'))
        return {
            method['id']: method
            for dimension in registry['dimensions']
            for method in dimension['methods']
        }
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise SystemExit(f'无法读取方法注册表: {exc}')


def validate_result(result: object) -> None:
    if not isinstance(result, dict):
        raise SystemExit('result必须为对象')
    p_value = result.get('p_value')
    if p_value is not None and (not isinstance(p_value, (int, float)) or not 0 <= p_value <= 1):
        raise SystemExit('result.p_value必须为0到1之间的数值或null')
    for key in ('n', 'clusters'):
        value = result.get(key)
        if value is not None and (not isinstance(value, int) or value < 0):
            raise SystemExit(f'result.{key}必须为非负整数或null')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', required=True)
    ap.add_argument('--entry', required=True)
    ap.add_argument('--registry', default=str(Path(__file__).resolve().parents[1] / 'references' / 'method-registry.json'))
    args = ap.parse_args()

    entry = json.loads(Path(args.entry).read_text(encoding='utf-8'))
    missing = [key for key in REQ if key not in entry]
    if missing:
        raise SystemExit('缺少字段: ' + ', '.join(missing))
    if entry['adjustment_level'] not in ['A', 'B', 'C', 'D']:
        raise SystemExit('adjustment_level必须为A/B/C/D')
    if not isinstance(entry['decision_used_p_value'], bool):
        raise SystemExit('decision_used_p_value必须为true或false')
    validate_result(entry['result'])

    methods = registry_index(Path(args.registry))
    method = methods.get(entry['method_id'])
    if method is None:
        raise SystemExit(f"未知method_id: {entry['method_id']}")
    if entry['adjustment_level'] != method['adjustment_level']:
        raise SystemExit('adjustment_level必须与方法注册表一致')
    if entry['method_id'].startswith('baseline_') and entry['decision_used_p_value']:
        raise SystemExit('基准模型不能依据p值作出决策')

    entry.setdefault('timestamp', datetime.now(timezone.utc).isoformat())
    if entry['decision_used_p_value']:
        raise SystemExit('依据p值选择规格不得作为已批准运行写入日志；请记录为未批准的审计事件，而非把方法等级改写为D。')

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        prior_ids = {
            json.loads(line)['run_id']
            for line in log_path.read_text(encoding='utf-8').splitlines()
            if line.strip()
        }
        if entry['run_id'] in prior_ids:
            raise SystemExit(f"run_id已存在，拒绝覆盖审计记录: {entry['run_id']}")
    with log_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(json.dumps({
        'status': 'appended',
        'run_id': entry['run_id'],
        'level': entry['adjustment_level']
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
