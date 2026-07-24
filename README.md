# Empirical Significance Adjustment Skill

一个面向Stata/经济金融实证研究的“规范化显著性诊断与调整”Agent Skill。

## 能做什么

- 复现并锁定基准回归
- 诊断数据、变量、模型、固定效应、聚类和统计功效问题
- 将常用的方法映射为可调用的方法注册表
- 为每项方法提供适用条件、限制、Stata示例、输入输出和报告字段
- 记录全部规格尝试，生成可审计报告

## 结构

```text
empirical-significance-adjustment-skill/
├── SKILL.md
├── AGENTS.md
├── references/
│   ├── method-registry.json
│   ├── method-catalog.md
│   ├── decision-rules.md
│   ├── reporting-and-audit.md
│   └── source-map.md
├── assets/
│   ├── project.schema.json
│   ├── adjustment-entry.schema.json
│   ├── example-project.json
│   └── final-report-template.md
├── scripts/
│   ├── validate_project.py
│   ├── initialize_run.py
│   ├── append_adjustment_log.py
│   ├── generate_plan.py
│   └── summarize_run.py
├── templates/stata/
│   ├── 00_config.do
│   ├── 01_preflight.do
│   ├── 02_baseline.do
│   └── 03_adjustment_matrix.do
├── examples/
│   └── chain-policy-project.json
└── evals/evals.json
```

## 最快使用

```bash
python scripts/validate_project.py assets/example-project.json
python scripts/initialize_run.py --project assets/example-project.json --out run-output
python scripts/generate_plan.py --project run-output/project.json --registry references/method-registry.json --out run-output/adjustment_plan.md
```

在Stata复现基准模型后，先将包含完整结果的基准记录锁定，再把它和后续已批准规格追加到日志：

```bash
python scripts/lock_baseline_result.py --run-dir run-output --entry baseline-result.json
python scripts/append_adjustment_log.py --log run-output/adjustment_log.jsonl --entry baseline-result.json
python scripts/append_adjustment_log.py --log run-output/adjustment_log.jsonl --entry approved-result.json
```

在Agent中安装时，将整个文件夹复制到该Agent支持的skills目录。不同客户端目录不同，但均以根目录中的`SKILL.md`作为入口。

## 设计原则

- 显著性是诊断目标之一，但不是规格选择的唯一标准。
- 允许修复数据、测量和模型问题以恢复合理显著性。
- 每次调整必须说明为什么更准确、更符合理论或更匹配数据。
- 不隐藏失败结果；报告尝试总数、样本变化和推断变化。
