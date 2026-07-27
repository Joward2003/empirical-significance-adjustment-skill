#!/usr/bin/env python3
"""Generate a non-executable diagnostic plan from validated project flags."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_utils import load_project, registry_index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    project = load_project(Path(args.project))
    index = registry_index(Path(args.registry))
    flags = project.get("diagnostic_flags", {})
    selected: list[str] = []
    pending: list[str] = []
    outcome = project.get("outcome", {})
    exposure = project.get("core_exposure", {})
    if flags.get("few_clusters"):
        selected.append("wild_cluster_bootstrap")
    if flags.get("outcome_many_zeros"):
        if outcome.get("has_negatives"):
            selected.append("asinh_transform")
        else:
            pending.append("D07：零值本身不足以决定 ln(1+y) 或 IHS；先根据变量单位、分布和可解释性选择。")
    if flags.get("staggered_policy"):
        if exposure.get("type") == "did":
            selected.append("did_family")
        else:
            pending.append("D09：标记为交错政策，但核心变量不是DID；先核对处理定义。")
    if flags.get("measurement_error_concern"):
        pending.append("D11：先确认候选代理测量同一经济概念、口径可比且可报告共同样本；不要自动替换为企业绩效或创新指标。")
    if flags.get("special_years"):
        pending.append("D05：须先登记具体异常年份及其独立制度/数据口径依据；不能自动排除年份。")
    if flags.get("bad_control_concern"):
        pending.append("D02：逐项标记处理后变量、中介、机械构成变量和缺失机制；再预先定义可比较的控制组。")

    allowed = set(project.get("allowed_adjustment_levels", ["A", "B", "C"]))
    selected = [method_id for method_id in dict.fromkeys(selected) if index[method_id]["adjustment_level"] in allowed]
    lines = [
        "# 自动生成的调整计划",
        "",
        f"项目：{project['project_id']}",
        "",
        "> 该计划只基于配置中的诊断flags生成，不构成执行授权。每一项均须补充独立诊断证据、所需输入和研究者批准后才可运行。",
        "",
        "| 顺序 | method_id | 等级 | 方法 | 目的 | 主要限制 |",
        "|---:|---|---|---|---|---|",
    ]
    for order, method_id in enumerate(selected, 1):
        method = index[method_id]
        lines.append(
            f"| {order} | `{method_id}` | {method['adjustment_level']} | {method['title_zh']} | "
            f"{method['purpose']} | {'；'.join(method['use_restrictions'])} |"
        )
    lines += ["", "## 待补充的诊断（未生成可执行规格）", ""]
    lines.extend(f"- {item}" for item in pending) if pending else lines.append("- 无。仍须在执行前记录每项候选方法的诊断证据与批准人。")
    lines += ["", "## 代码草案", ""]
    for method_id in selected:
        method = index[method_id]
        lines += [f"### {method_id}｜{method['title_zh']}", "```stata", method["stata_code"], "```", ""]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "out": str(out), "method_count": len(selected)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
