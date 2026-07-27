#!/usr/bin/env python3
"""Release checks for metadata, references, schemas, and bundled fixtures."""
from __future__ import annotations

import json
import re
from pathlib import Path

from audit_utils import ROOT, load_json, registry_index, validate_approved_entry


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^name:\s*([^\s]+)\s*$", skill, re.MULTILINE)
    if not match or match.group(1) != ROOT.name:
        fail("SKILL.md frontmatter name必须与父目录名称一致")
    for relative in (
        "references/audit-model.md",
        "assets/project.schema.json",
        "assets/adjustment-entry.schema.json",
        "assets/audit-event.schema.json",
        "assets/final-report-template.md",
        "scripts/append_audit_event.py",
        "scripts/verify_run_integrity.py",
        "tests/test_workflow.py",
    ):
        if not (ROOT / relative).exists():
            fail(f"缺少必需文件: {relative}")

    registry = load_json(ROOT / "references" / "method-registry.json", "方法注册表")
    evals = load_json(ROOT / "evals" / "evals.json", "评测配置")
    if registry.get("skill_name") != match.group(1) or evals.get("skill_name") != match.group(1):
        fail("registry/evals中的skill_name与frontmatter不一致")
    methods = registry_index()
    if len(methods) != sum(len(dimension.get("methods", [])) for dimension in registry.get("dimensions", [])):
        fail("方法注册表存在空method_id或重复method_id")
    for dimension in registry.get("dimensions", []):
        if not re.fullmatch(r"D\d{2}", dimension.get("id", "")):
            fail("方法注册表包含无效dimension id")
    catalog = (ROOT / "references" / "method-catalog.md").read_text(encoding="utf-8")
    catalog_ids = set(re.findall(r"^### `([^`]+)`", catalog, re.MULTILINE))
    if catalog_ids != set(methods):
        fail("method-catalog.md与method-registry.json的method_id不一致")
    eval_ids = [item.get("id") for item in evals.get("evals", [])]
    if len(eval_ids) != len(set(eval_ids)) or not any(item.get("should_activate") is False for item in evals["evals"]):
        fail("evals必须有唯一ID并包含至少一个反触发测试")

    validate_approved_entry(load_json(ROOT / "tests" / "fixtures" / "baseline-result.json", "baseline fixture"), methods)
    validate_approved_entry(load_json(ROOT / "tests" / "fixtures" / "approved-result.json", "approved fixture"), methods)
    headings = re.findall(r"^## (.+)$", (ROOT / "assets" / "final-report-template.md").read_text(encoding="utf-8"), re.MULTILINE)
    if len(headings) != 10:
        fail("最终报告模板必须保留十个章节")
    print(json.dumps({"valid": True, "dimensions": len(registry["dimensions"]), "methods": len(methods), "evals": len(eval_ids)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
