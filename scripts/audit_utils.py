#!/usr/bin/env python3
"""Shared validation and hash-chain helpers for auditable empirical runs."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APPROVED_STATUSES = {"supports", "directional_imprecise", "sensitive", "opposite"}
NULL_RESULT_STATUSES = {"failed", "not_run"}


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"无法读取{label}: {exc}")
    if not isinstance(value, dict):
        raise SystemExit(f"{label}必须是JSON对象")
    return value


def entry_identity_hash(entry: dict) -> str:
    """Stable identity used to bind a pre-logged baseline to its later log entry."""
    payload = {k: v for k, v in entry.items() if k not in {"timestamp", "previous_entry_sha256", "entry_sha256"}}
    return sha256_bytes(canonical_json(payload))


def chained_entry_hash(entry: dict) -> str:
    payload = {k: v for k, v in entry.items() if k != "entry_sha256"}
    return sha256_bytes(canonical_json(payload))


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise SystemExit(f"缺少jsonschema依赖；请运行: python -m pip install -r requirements.txt ({exc})")
    schema = load_json(schema_path, f"{label} Schema")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors[:5]
        )
        raise SystemExit(f"{label}不符合JSON Schema: {details}")


def load_project(path: Path) -> dict:
    project = load_json(path, "项目配置")
    validate_schema(project, ROOT / "assets" / "project.schema.json", "项目配置")
    period = project["sample_period"]
    if period["start"] > period["end"]:
        raise SystemExit("sample_period.start不能晚于end")
    return project


def registry_index(path: Path | None = None) -> dict[str, dict]:
    registry_path = path or ROOT / "references" / "method-registry.json"
    registry = load_json(registry_path, "方法注册表")
    try:
        methods = {
            method["id"]: method
            for dimension in registry["dimensions"]
            for method in dimension["methods"]
        }
    except (KeyError, TypeError) as exc:
        raise SystemExit(f"方法注册表结构无效: {exc}")
    if not methods:
        raise SystemExit("方法注册表不能为空")
    return methods


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_result_semantics(entry: dict) -> None:
    result = entry["result"]
    status = entry["status"]
    values = [result[name] for name in ("beta", "se", "p_value", "ci_low", "ci_high", "n", "clusters")]
    if status in APPROVED_STATUSES and any(value is None for value in values):
        raise SystemExit("已估计的运行必须完整记录beta、SE、p、95%CI、N和clusters")
    if status in NULL_RESULT_STATUSES and any(value is not None for value in values):
        raise SystemExit("failed或not_run运行的result字段必须全部为null")
    for name, value in result.items():
        if value is not None and not _is_finite_number(value):
            raise SystemExit(f"result.{name}必须是有限数值或null")
    low, high = result["ci_low"], result["ci_high"]
    if (low is None) != (high is None):
        raise SystemExit("ci_low与ci_high必须同时提供或同时为null")
    if low is not None and low > high:
        raise SystemExit("ci_low不能大于ci_high")


def validate_approved_entry(entry: dict, registry: dict[str, dict]) -> None:
    validate_schema(entry, ROOT / "assets" / "adjustment-entry.schema.json", "调整记录")
    validate_result_semantics(entry)
    method = registry.get(entry["method_id"])
    if method is None:
        raise SystemExit(f"未知method_id: {entry['method_id']}")
    if entry["adjustment_level"] != method["adjustment_level"]:
        raise SystemExit("adjustment_level必须与方法注册表一致")


def validate_audit_event(event: dict, project: dict, project_sha256: str, registry: dict[str, dict]) -> None:
    validate_schema(event, ROOT / "assets" / "audit-event.schema.json", "审计事件")
    if event["project_id"] != project["project_id"] or event["project_sha256"] != project_sha256:
        raise SystemExit("审计事件未绑定当前项目或项目哈希")
    method = registry.get(event["method_id"])
    if method is None:
        raise SystemExit(f"审计事件包含未知method_id: {event['method_id']}")
    if event["adjustment_level"] != method["adjustment_level"]:
        raise SystemExit("审计事件adjustment_level必须与方法注册表一致")
    if event["event_type"] == "rejected_specification" and event.get("decision_used_p_value") is not True:
        raise SystemExit("rejected_specification必须明确标记decision_used_p_value=true")
    observed = event.get("observed_result")
    if observed is not None:
        if "p_value" in observed and (not _is_finite_number(observed["p_value"]) or not 0 <= observed["p_value"] <= 1):
            raise SystemExit("审计事件observed_result.p_value必须为0到1之间的有限数值")
        for name in ("se", "n", "clusters"):
            if name in observed and observed[name] is not None:
                if not _is_finite_number(observed[name]):
                    raise SystemExit(f"审计事件observed_result.{name}必须为有限数值或null")
                if observed[name] <= 0:
                    raise SystemExit(f"审计事件observed_result.{name}必须大于0")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}不是有效JSON: {exc}")
        if not isinstance(row, dict):
            raise SystemExit(f"{path}:{line_no}必须是JSON对象")
        rows.append(row)
    return rows


def verify_chain(rows: list[dict], label: str) -> None:
    previous = None
    for index, row in enumerate(rows, 1):
        if row.get("previous_entry_sha256") != previous:
            raise SystemExit(f"{label}第{index}条previous_entry_sha256不匹配")
        actual = chained_entry_hash(row)
        if row.get("entry_sha256") != actual:
            raise SystemExit(f"{label}第{index}条entry_sha256不匹配；日志可能被修改")
        previous = actual
