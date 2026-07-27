# Empirical Inference Diagnostics Skill

一个面向经济、金融与政策实证研究的 Codex Skill：诊断不显著、方向不稳定或规格敏感的估计，
生成可复现的推断与稳健性分析方案，并保留完整审计路径。

它不是“把结果调显著”的工具。任何模型、样本、聚类、控制、阈值或变换都必须有独立于
最终 p 值的理论或诊断依据。

## 适用范围

当用户问“回归为什么不显著”“标准误为何异常”“固定效应/聚类/控制/样本窗口为何改变结果”
时使用。一般 Stata 语法、一般 DID/IV/PSM 概念介绍不应触发此 Skill。

## 安装到 Codex

将仓库目录放入 Codex 的 Skill 搜索目录，并保持目录名与 frontmatter 一致：

```text
~/.codex/skills/empirical-significance-adjustment-skill/
├── SKILL.md
├── references/
├── assets/
└── scripts/
```

首次使用审计脚本前安装依赖：

```bash
python -m pip install -r requirements.txt
```

## 审计工作流

```bash
python scripts/validate_project.py assets/example-project.json
python scripts/initialize_run.py --project assets/example-project.json --out run-output
python scripts/generate_plan.py --project run-output/project.json --registry references/method-registry.json --out run-output/adjustment_plan.md

# 在 Stata 中复现基准后：
python scripts/lock_baseline_result.py --run-dir run-output --entry baseline-result.json
python scripts/append_adjustment_log.py --log run-output/adjustment_log.jsonl --entry baseline-result.json
python scripts/append_adjustment_log.py --log run-output/adjustment_log.jsonl --entry approved-result.json

# 已事后看过 p 值的规格只能作为审计事件记录：
python scripts/append_audit_event.py --run-dir run-output --event rejected-attempt.json

python scripts/verify_run_integrity.py --run-dir run-output
python scripts/summarize_run.py --project run-output/project.json --log run-output/adjustment_log.jsonl --out run-output/report.md
```

`summarize_run.py` 使用 [final-report-template.md](assets/final-report-template.md) 的十个章节生成最终报告。

## 研究诚信规则

- 先复现、锁定基准，再讨论模型调整。
- 不因 p 值更小而降低聚类层级、删控制、删样本或改阈值。
- 不隐藏合理但不显著、反向或无法估计的规格。
- 事后 p 值选择写入 `audit_events.jsonl`，不写入批准日志。
- 报告同时展示系数、SE、p、95% CI、样本和聚类数，以及相对基准的变化来源。

详见 [决策规则](references/decision-rules.md) 与 [报告和审计规则](references/reporting-and-audit.md)。

## 目录

```text
empirical-significance-adjustment-skill/
├── SKILL.md                         # Codex 入口与工作流
├── AGENTS.md                        # 仓库级操作规则
├── references/                      # 决策规则、方法目录、来源与审计边界
├── assets/                          # JSON Schema、项目示例与报告模板
├── scripts/                         # 验证、审计、报告与完整性检查
├── templates/stata/                 # 保守的 Stata 工作流模板
├── tests/                           # 端到端与负面路径测试
└── .github/workflows/ci.yml         # GitHub Actions 校验
```

## 哈希与完整性

SHA-256 哈希是文件内容的“数字指纹”。本项目用它绑定项目、方法注册表、基准快照和两条
追加式 JSONL 日志；它能检测常规编辑，但不是外部数字签名，也无法阻止能重写全部本地文件
的一方伪造整套记录。具体边界与外部存档建议见 [审计模型](references/audit-model.md) 和
[安全政策](SECURITY.md)。

## 开发与贡献

```bash
python scripts/test_repository_integrity.py
python -m unittest discover -s tests -v
git diff --check
```

贡献规则见 [CONTRIBUTING.md](CONTRIBUTING.md)。
