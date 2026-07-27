---
name: empirical-significance-adjustment-skill
description: >-
  诊断实证研究中不显著、方向不稳定或对模型设定敏感的估计结果，并生成透明、
  可复现的统计推断、稳健性分析和规格审计方案。仅当用户询问回归为何不显著、
  标准误异常、系数对控制变量、固定效应、聚类、滞后或样本窗口敏感时使用。
  不用于一般Stata语法教学或一般计量方法介绍，不得仅依据p值选择模型、样本、
  变量、聚类层级、阈值或变换方式。
license: See LICENSE
compatibility: >-
  Requires Python 3.9+ and the dependency listed in requirements.txt for audit scripts;
  generated Stata code requires user-side Stata and method-specific community packages.
metadata:
  version: 1.1.0
  language: zh-CN
  domain: empirical-economics
---

# 规范化显著性诊断与调整

## 目标

当理论方向明确但结果不显著时，判断问题是否来自数据错误、测量误差、模型不匹配、
固定效应、聚类推断、控制变量、传导期、样本窗口、极端值、指标构造或统计功效，
并在透明、可复现的前提下生成合理调整方案、Stata代码和审计报告。

本Skill可以主动寻找估计准确性、统计功效与推断可靠性的改善；每项调整必须有独立于最终
p值的诊断或理论依据，不能把“显著”作为规格选择目标。

## 触发后先读取

1. 读取 `references/decision-rules.md`，确定调整等级和边界。
2. 根据问题维度读取 `references/method-catalog.md`；需要机器筛选时读取 `references/method-registry.json`。
3. 需要生成最终材料时读取 `references/reporting-and-audit.md`、`references/audit-model.md` 和 `assets/final-report-template.md`。
4. 用户追问方法是否来自原文时读取 `references/source-map.md`。

## 必要输入

优先从用户文件、代码和现有结果中提取，不要重复询问已知信息：

- 研究问题与理论预期方向
- 观测单位、面板频率和样本期
- 因变量及其类型：连续、比例、计数、二元、含零/负值
- 核心解释变量或处理变量、构造公式和赋值层级
- 基准控制变量、固定效应和聚类层级
- 当前Stata代码、回归表或日志
- 数据处理流程：合并、缺失、缩尾、平减、滞后、ST处理
- 研究者允许的调整范围及预设/探索性边界

信息不足时，先输出“最小可执行诊断计划”，而不是随意猜测完整模型。

## 工作流

### 1. 复现并锁定基准

- 原样复现用户当前模型。
- 保存基准代码、估计样本、beta、SE、p、95% CI、N、聚类数和warning。
- 将基准写入一次性锁定的baseline snapshot；哈希链可检测后续编辑，但不是外部数字签名。
- 在看到后续结果前，明确哪些调整属于预设，哪些属于探索性。

### 2. 数据优先诊断

依次检查：

- 面板键是否唯一；merge是否一对一或符合预期
- 年份、企业、城市、行业代码是否错位或跨期变更
- 缺失值是否被错误填0；比例分母是否正确
- 政策时点和处理状态是否异常反复
- 金额单位、价格平减、正负方向和变量公式
- 极端值是录入错误还是有效高影响观测
- 滞后是否在非连续年份中错误生成

发现明确错误时，归类为A层调整，先修复再讨论模型。

### 3. 诊断不显著来源

判断主要问题属于：

- 测量误差或代理变量过粗
- 因变量分布与估计器不匹配
- 固定效应不足、过度或吸收识别变异
- 聚类层级与处理赋值/误差相关结构不匹配
- 坏控制、中介控制、共线性或缺失导致样本变化
- 政策传导存在滞后
- 样本期受重大冲击或口径变化
- 平均效应掩盖理论异质性
- 有效处理组、聚类数或组内变异不足

### 4. 生成调整计划再执行

对每个候选方法输出：

- method_id与调整等级
- 诊断证据
- 理论/统计依据
- 所需输入
- Stata代码
- 预期改变beta、SE还是样本
- 使用限制
- 必须报告的字段

未经计划不得批量搜索规格。

### 5. 执行并逐项记录

每次运行写入adjustment log。使用：

```bash
python scripts/initialize_run.py --project assets/example-project.json --out run-output
python scripts/lock_baseline_result.py --run-dir run-output --entry baseline-result.json
python scripts/append_adjustment_log.py --log run-output/adjustment_log.jsonl --entry result.json
python scripts/append_audit_event.py --run-dir run-output --event rejected-attempt.json
python scripts/verify_run_integrity.py --run-dir run-output
python scripts/summarize_run.py --project run-output/project.json --log run-output/adjustment_log.jsonl --out run-output/report.md
```

先用 `lock_baseline_result.py` 将已复现的基准结果一次性写入快照，再将同一条基准记录追加到日志；快照已锁定时必须新建运行目录。若发现某个规格是依据其p值事后选择的，不得把它伪装为“已批准调整”；应停止将其作为主分析并在最终报告的研究诚信部分说明。

如果用户只需要代码，仍需在代码注释中保留方法ID、理由和报告要求。

若某个规格已因观察到更小的p值而被尝试，不得把它写入批准结果日志；使用
`scripts/append_audit_event.py` 写入 `audit_events.jsonl`，以便报告“曾经尝试但未获批准”的事实。
生成最终报告前运行 `scripts/verify_run_integrity.py`，验证项目、注册表、baseline快照、Schema和两条日志的哈希链。最终报告必须由 `summarize_run.py` 按 `assets/final-report-template.md` 的完整章节生成。

### 6. 分解显著性变化

比较基准与调整模型：

- beta是否变化
- SE是否变化
- N和聚类数是否变化
- 变化是否主要来自聚类放松、样本筛选或代理定义

不能只写“调整后显著”。必须说明显著性改善的来源和风险。

### 7. 输出全部结果

- 不隐藏不显著、反向或无法估计的合理规格。
- 同时报告p值、95% CI和经济量级。
- 多窗口、多阈值、多结果变量或多子样本时，说明尝试总数和多重检验风险。
- 异质性优先报告交互项与正式差异检验。

## 方法路由

| 用户问题 | 优先读取/方法维度 |
|---|---|
| 聚类后不显著、标准误很大 | D01 标准误与聚类；检查赋值层级和聚类数 |
| 加控制后不显著 | D02 控制变量；检查坏控制、缺失和共线性 |
| 换固定效应后消失 | D04 固定效应；检查识别变异是否被吸收 |
| 政策当期不显著 | D06 滞后；D09 DID动态效应 |
| 大量零、偏态或极端值 | D07 变换/缩尾；先检查数据错误 |
| 想换因变量或代理 | D11 替代衡量；保持共同样本对比 |
| 想删年份、地区或行业 | D05/D15；必须有独立依据并报告全路径 |
| 想按中位数分组 | D10/D15；保留连续设定并做组间差异检验 |
| 综合指数不显著 | D12/D14；检查正向化、标准化、权重和相关性 |
| ST样本怎么处理 | D13；基准与严格样本配对报告 |

## 硬性规则

- 不因p值更小而降低聚类层级。
- 不因p值更小而删除控制变量、年份、地区、行业或观测。
- 不反复改变缩尾比例、阈值、滞后期或行业粒度直到显著。
- 不把标准化当作能独立改变线性模型显著性的手段。
- 不把一个子样本显著、另一个不显著直接解释为组间差异。
- 不把滞后、PSM、Heckman或IV自动表述为解决内生性；逐项检查前提。
- 不只输出最终选定模型；保留模型尝试总表和失败结果。

## 默认输出

1. **诊断摘要**：最可能的不显著来源及证据。
2. **优先调整计划**：A/B/C层排序，附方法ID和代码。
3. **调整结果总表**：全部尝试、系数、SE、p、CI、N、聚类数。
4. **显著性来源分解**：beta/SE/样本变化。
5. **风险与限制**：识别、推断、样本选择和多重尝试。
6. **结论等级**：A/B/C/D/E。
7. **复现包**：Stata代码、配置、日志、报告。

## 完成条件

- [ ] 基准结果可复现且未被覆盖
- [ ] 数据诊断已完成或明确指出无法完成的部分
- [ ] 每项调整有method_id、依据和等级
- [ ] 全部合理尝试均在日志中
- [ ] 样本、聚类、控制和固定效应变化可追溯
- [ ] 报告包括95% CI与经济量级
- [ ] 结论没有超过识别设计支持的范围
