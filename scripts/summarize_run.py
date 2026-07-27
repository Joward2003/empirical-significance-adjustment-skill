#!/usr/bin/env python3
"""Render a complete final report using the repository's report template headings."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit_utils import ROOT, sha256_file
from verify_run_integrity import verify_run_dir


EXPECTED_HEADINGS = [
    "1. 项目信息",
    "2. 基准模型复现",
    "3. 数据与模型诊断",
    "4. 调整计划",
    "5. 全部调整结果",
    "6. 显著性改善来源分解",
    "7. 稳健性、敏感性与失败结果",
    "8. 多重尝试与研究诚信说明",
    "9. 结论等级",
    "10. 复现文件",
]


def markdown(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def fnum(value: object, digits: int = 3) -> str:
    return "" if value is None else f"{float(value):.{digits}f}"


def pct(new: object, base: object) -> float | None:
    if new is None or base in (None, 0):
        return None
    return (float(new) - float(base)) / abs(float(base)) * 100


def fpct(value: float | None) -> str:
    return "" if value is None else f"{value:.1f}%"


def change_source(beta_change: float | None, se_change: float | None, sample_change: float | None) -> str:
    candidates = {
        "系数变化": abs(beta_change or 0),
        "标准误变化": abs(se_change or 0),
        "样本变化": abs(sample_change or 0),
    }
    source, magnitude = max(candidates.items(), key=lambda item: item[1])
    return source if magnitude >= 5 else "变化较小；不宜归因"


def conclusion_grade(entries: list[dict]) -> str:
    statuses = {status: sum(entry["status"] == status for entry in entries) for status in {
        "supports", "directional_imprecise", "sensitive", "opposite", "failed", "not_run"
    }}
    if any(entry["adjustment_level"] == "D" for entry in entries):
        return "D（存在高风险规格；不能作为主结论）"
    if statuses["supports"] == 0:
        return "E（已记录的运行未形成精确支持）"
    return "待人工分级（A/B/C取决于纠错证据、识别前提和完整敏感性）"


def template_headings(path: Path) -> list[str]:
    headings = re.findall(r"^## (.+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
    if headings != EXPECTED_HEADINGS:
        raise SystemExit("final-report-template.md的十个章节标题已变化；请先更新summarize_run.py的渲染映射。")
    return headings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Path to run-output/project.json")
    parser.add_argument("--log", required=True, help="Path to run-output/adjustment_log.jsonl")
    parser.add_argument("--out", required=True)
    parser.add_argument("--template", default=str(ROOT / "assets" / "final-report-template.md"))
    parser.add_argument("--registry", default=None)
    args = parser.parse_args()

    log_path = Path(args.log)
    run_dir = log_path.parent
    if Path(args.project).resolve() != (run_dir / "project.json").resolve():
        raise SystemExit("--project必须指向与--log同一运行目录中的project.json。")
    headings = template_headings(Path(args.template))
    project, _snapshot, entries, events = verify_run_dir(run_dir, Path(args.registry) if args.registry else None)
    baseline = entries[0]
    base_result = baseline["result"]
    baseline_spec = project["baseline_specification"]
    plan_path = run_dir / "adjustment_plan.md"
    grade = conclusion_grade(entries)

    lines = ["# 规范化实证推断诊断与规格审计报告", "", "> 本报告由 `assets/final-report-template.md` 的章节结构生成。哈希链可检测运行后编辑，但不构成外部签名或绝对不可篡改保证。", ""]

    lines += [f"## {headings[0]}", "", f"- 项目ID：{markdown(project['project_id'])}", f"- 研究问题：{markdown(project['research_question'])}", f"- 理论方向：{markdown(project.get('theory_direction', 'unknown'))}", f"- 观测单位与样本期：{markdown(project['unit_of_observation'])}；{project['sample_period']['start']}–{project['sample_period']['end']}", f"- 软件：{markdown(project['software'])}", f"- 预分析计划：{markdown(project.get('pre_analysis_plan', '未提供'))}", f"- 多重检验计划：{markdown(project.get('multiple_testing_plan', '未提供'))}", ""]

    ci = f"[{fnum(base_result['ci_low'])}, {fnum(base_result['ci_high'])}]"
    lines += [f"## {headings[1]}", "", f"- 因变量：{markdown(project['outcome']['name'])}", f"- 核心变量：{markdown(project['core_exposure']['name'])}", f"- 控制变量：{markdown(', '.join(baseline_spec['controls']))}", f"- 固定效应：{markdown(', '.join(baseline_spec['fixed_effects']))}", f"- 聚类层级与聚类数：{markdown(', '.join(baseline_spec['cluster']))}；{base_result['clusters']}", f"- Stata代码：`{markdown(baseline.get('code'))}`", f"- beta / SE / p / 95% CI / N：{fnum(base_result['beta'])} / {fnum(base_result['se'])} / {fnum(base_result['p_value'])} / {ci} / {base_result['n']}", f"- warning与被删除观测：{markdown('；'.join(baseline.get('warnings', [])) or '未记录')}", ""]

    lines += [f"## {headings[2]}", "", "| 诊断维度 | 已记录证据 | 风险 | 是否需要调整 |", "|---|---|---|---|"]
    diagnostic_rows = [
        ("数据键与合并", "未在结构化日志中单列记录", "待人工核验", "视数据诊断而定"),
        ("变量构造与单位", "未在结构化日志中单列记录", "待人工核验", "视数据诊断而定"),
        ("因变量分布", "; ".join(entry["rationale"] for entry in entries if "transform" in entry["method_id"]) or "未记录", "待人工核验", "视诊断而定"),
        ("固定效应与识别变异", "; ".join(entry["rationale"] for entry in entries if "fe" in entry["method_id"]) or "未记录", "待人工核验", "视诊断而定"),
        ("聚类与赋值层级", "; ".join(entry["rationale"] for entry in entries if "cluster" in entry["method_id"]) or "未记录", "待人工核验", "视诊断而定"),
        ("控制变量与坏控制", "; ".join(entry["rationale"] for entry in entries if "control" in entry["method_id"]) or "未记录", "待人工核验", "视诊断而定"),
        ("传导期", "; ".join(entry["rationale"] for entry in entries if "lag" in entry["method_id"]) or "未记录", "待人工核验", "视诊断而定"),
        ("统计功效", "; ".join(item for entry in entries for item in entry["diagnostic_evidence"]) or "未记录", "待人工核验", "视诊断而定"),
    ]
    lines.extend(f"| {markdown(name)} | {markdown(evidence)} | {risk} | {need} |" for name, evidence, risk, need in diagnostic_rows)
    lines += [""]

    lines += [f"## {headings[3]}", "", "| 序号 | method_id | 等级 | analysis_stage | 诊断依据 | 预期改变 | 使用限制 |", "|---:|---|---|---|---|---|---|"]
    for order, entry in enumerate(entries[1:], 1):
        lines.append(f"| {order} | {entry['method_id']} | {entry['adjustment_level']} | {entry['analysis_stage']} | {markdown('；'.join(entry['diagnostic_evidence']))} | 见相对基准变化 | 见注册表与rationale |")
    if len(entries) == 1:
        lines.append("| — | — | — | — | 尚无批准调整 | — | — |")
    lines += [f"", f"- 计划文件：{'`adjustment_plan.md`（已存在）' if plan_path.exists() else '未提供；报告仅反映已写入日志的运行。'}", ""]

    lines += [f"## {headings[4]}", "", "| run_id | method_id | beta | SE | p | 95% CI | N | clusters | 状态 | 备注 |", "|---|---|---:|---:|---:|---|---:|---:|---|---|"]
    for entry in entries:
        result = entry["result"]
        ci = f"[{fnum(result['ci_low'])}, {fnum(result['ci_high'])}]" if result["ci_low"] is not None else ""
        lines.append(f"| {entry['run_id']} | {entry['method_id']} | {fnum(result['beta'])} | {fnum(result['se'])} | {fnum(result['p_value'])} | {ci} | {markdown(result['n'])} | {markdown(result['clusters'])} | {entry['status']} | {markdown('；'.join(entry.get('warnings', [])) or entry['rationale'])} |")
    lines += [""]

    lines += [f"## {headings[5]}", "", "| run_id | beta变化% | SE变化% | N变化% | 主要来源 | 风险判断 |", "|---|---:|---:|---:|---|---|"]
    for entry in entries:
        result = entry["result"]
        beta_change = pct(result["beta"], base_result["beta"])
        se_change = pct(result["se"], base_result["se"])
        n_change = pct(result["n"], base_result["n"])
        risk = "高" if entry["adjustment_level"] == "D" else ("中" if entry["adjustment_level"] == "C" else "低/中")
        lines.append(f"| {entry['run_id']} | {fpct(beta_change)} | {fpct(se_change)} | {fpct(n_change)} | {change_source(beta_change, se_change, n_change)} | {risk} |")
    lines += [""]

    status_counts = {status: sum(entry["status"] == status for entry in entries) for status in {"supports", "directional_imprecise", "sensitive", "opposite", "failed", "not_run"}}
    lines += [f"## {headings[6]}", "", f"- 方向稳定性：supports={status_counts['supports']}；directional_imprecise={status_counts['directional_imprecise']}；opposite={status_counts['opposite']}。", f"- 量级范围：见“全部调整结果”与“显著性改善来源分解”。", f"- 聚类敏感性：需依据含聚类变更的已批准规格人工判断。", f"- 样本敏感性：需依据含样本变更的已批准规格人工判断。", f"- 代理变量敏感性：需依据替代代理的已批准规格人工判断。", f"- 失败或反向结果：failed={status_counts['failed']}；not_run={status_counts['not_run']}；opposite={status_counts['opposite']}。", ""]

    stage_counts = {stage: sum(entry["analysis_stage"] == stage for entry in entries) for stage in {"pre_registered", "pre_specified", "exploratory"}}
    lines += [f"## {headings[7]}", "", f"- 总模型数：{len(entries)}", f"- 预注册模型数：{stage_counts['pre_registered']}", f"- 预先指定模型数：{stage_counts['pre_specified']}", f"- 探索模型数：{stage_counts['exploratory']}", "- 多结果/窗口/阈值/子样本数量：未在当前结构化日志中单列标记。", f"- 是否进行了多重检验或规格曲线：{markdown(project.get('multiple_testing_plan', '未提供；如存在多规格探索，应在人工结论中补充。'))}", "- 是否存在依据p值作出的批准决策：否；批准记录Schema固定为false。", f"- 未批准/失败审计事件数：{len(events)}", "", "| event_id | method_id | 类型 | analysis_stage | 理由 | 观察到的结果 |", "|---|---|---|---|---|---|"]
    if events:
        for event in events:
            lines.append(f"| {event['event_id']} | {event['method_id']} | {event['event_type']} | {event['analysis_stage']} | {markdown(event['reason'])} | {markdown(event.get('observed_result'))} |")
    else:
        lines.append("| — | — | — | — | 无 | — |")
    lines += [""]

    lines += [f"## {headings[8]}", "", f"- 等级：{grade}", "- 可支持的结论：仅限于完整记录、具有独立诊断依据且通过识别与敏感性审查的结果。", "- 不可支持的结论：不能因单一显著规格、删样本、放松聚类或事后阈值选择而宣称因果效应。", "- 下一步数据或设计需求：补录结构化数据诊断、预设/探索标记、功效分析和必要的识别检验。", ""]

    files = [run_dir / name for name in ("project.json", "baseline_snapshot.json", "adjustment_log.jsonl", "audit_events.jsonl")]
    if plan_path.exists():
        files.append(plan_path)
    lines += [f"## {headings[9]}", "", "| 文件 | SHA-256 |", "|---|---|"]
    lines.extend(f"| {path.name} | `{sha256_file(path)}` |" for path in files)
    lines += ["", "- Stata do-file、输出表图：由研究者在运行目录外部保存后，须在提交或归档时一并列入。"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "out": str(out), "grade": grade}, ensure_ascii=False))


if __name__ == "__main__":
    main()
