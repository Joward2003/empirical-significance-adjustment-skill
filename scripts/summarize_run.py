#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def pct(new, base):
    if new is None or base in (None, 0):
        return None
    return (new - base) / abs(base) * 100


def fnum(value, digits=3):
    return '' if value is None else f'{value:.{digits}f}'


def fpct(value):
    return '' if value is None else f'{value:.1f}%'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--log', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    project = json.loads(Path(args.project).read_text(encoding='utf-8'))
    entries = []
    for line in Path(args.log).read_text(encoding='utf-8').splitlines():
        if line.strip():
            entries.append(json.loads(line))

    baseline_entries = [entry for entry in entries if entry['method_id'].startswith('baseline_')]
    if entries and len(baseline_entries) != 1:
        raise SystemExit('日志必须恰有一条method_id以baseline_开头的基准记录；拒绝把其他规格当作基准。')
    baseline = baseline_entries[0] if baseline_entries else None
    baseline_result = baseline.get('result', {}) if baseline else {}

    lines = [
        '# 规范化显著性诊断与调整运行报告',
        '',
        f"- 项目：{project['project_id']}",
        f"- 研究问题：{project['research_question']}",
        f"- 总运行数：{len(entries)}",
        f"- 使用p值参与决策的运行数：{sum(bool(e.get('decision_used_p_value')) for e in entries)}",
        '',
        '## 全部结果',
        '',
        '| run_id | method_id | level | beta | SE | p | 95% CI | N | clusters | status |',
        '|---|---|---|---:|---:|---:|---|---:|---:|---|',
    ]

    for entry in entries:
        result = entry.get('result', {})
        ci = ''
        if result.get('ci_low') is not None:
            ci = f"[{fnum(result.get('ci_low'))}, {fnum(result.get('ci_high'))}]"
        lines.append(
            f"| {entry['run_id']} | {entry['method_id']} | {entry['adjustment_level']} | "
            f"{fnum(result.get('beta'))} | {fnum(result.get('se'))} | "
            f"{fnum(result.get('p_value'))} | {ci} | {result.get('n', '')} | "
            f"{result.get('clusters', '')} | {entry['status']} |"
        )

    lines += [
        '',
        '## 相对基准的变化',
        '',
        '| run_id | beta变化 | SE变化 | N变化 | 风险 |',
        '|---|---:|---:|---:|---|',
    ]
    for entry in entries:
        result = entry.get('result', {})
        risk = (
            '高' if entry.get('decision_used_p_value') or entry['adjustment_level'] == 'D'
            else ('中' if entry['adjustment_level'] == 'C' else '低/中')
        )
        lines.append(
            f"| {entry['run_id']} | {fpct(pct(result.get('beta'), baseline_result.get('beta')))} | "
            f"{fpct(pct(result.get('se'), baseline_result.get('se')))} | "
            f"{fpct(pct(result.get('n'), baseline_result.get('n')))} | {risk} |"
        )

    statuses = {
        status: sum(entry['status'] == status for entry in entries)
        for status in ['supports', 'directional_imprecise', 'sensitive', 'opposite', 'failed', 'not_run']
    }
    high_risk = sum(entry['adjustment_level'] == 'D' for entry in entries)
    if not entries:
        grade = 'E（尚无运行结果）'
    elif high_risk:
        grade = 'D（存在高风险规格；需人工审查其是否为结果导向）'
    elif statuses['supports'] == 0:
        grade = 'E（已记录的运行未形成精确支持）'
    else:
        grade = '待人工分级（存在支持性结果，但A/B/C取决于纠错证据、识别前提与完整敏感性）'

    lines += [
        '',
        '## 自动结论等级',
        '',
        grade,
        '',
        '自动汇总不会仅按“显著结果数量”授予A/B/C等级；最终结论须结合纠错证据、识别设计、经济量级和完整诊断。',
    ]
    Path(args.out).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'written', 'out': args.out, 'grade': grade}, ensure_ascii=False))


if __name__ == '__main__':
    main()
