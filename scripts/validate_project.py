#!/usr/bin/env python3
"""Validate a project configuration before a run is initialized or planned."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_utils import load_project


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    args = parser.parse_args()
    project = load_project(Path(args.project))
    baseline = project["baseline_specification"]
    warnings = []
    if not baseline["cluster"]:
        warnings.append("未指定聚类层级")
    outcome = project["outcome"]
    if outcome.get("has_zeros") and outcome.get("type") == "continuous":
        warnings.append("连续因变量含零：检查对数/IHS处理")
    print(json.dumps({"valid": True, "project_id": project["project_id"], "warnings": warnings}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
