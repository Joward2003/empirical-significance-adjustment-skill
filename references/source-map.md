# 来源映射

## 用户提供PDF

### PDF 1：《Stata基准回归 + 调显著方法大全（一）》

- pp.1-2：企业、省份、城市、国家基准回归模板
- pp.2-3：聚类层级与控制变量
- p.4：标准化与固定效应
- p.5：样本起止时间和特殊年份
- p.6：滞后处理、对数变换
- p.7：二次项、IHS、缩尾、行业代码粒度
- p.8：行业粒度总结和声明

### PDF 2：《调显著方法大全（二）》

- pp.1-2：分位数回归、DID、RDD、门槛、PSM、Heckman、IV、SCM
- p.3：阈值赋值、中位数、区间和分位数组
- pp.4-5：企业绩效、数字化、融资约束、创新、环境绩效代理变量
- pp.5-7：熵值、TOPSIS、CRITIC、PCA、因子、灰色关联、变异系数
- pp.7-8：ST企业处理
- pp.8-9：逆指标正向化
- pp.9-10：企业、行业、地区和特殊样本策略
- p.11：两篇方法总结与声明

## GitHub结构参考

- `anthropics/skills`：采用“SKILL.md + scripts + references + assets”的渐进披露结构。
- `agentskills/agentskills`：采用Agent Skills开放格式，SKILL.md包含YAML frontmatter和Markdown指令。
- `brycewang-stanford/AER-Skills`：参考其把识别、执行、稳健性和报告拆成可审计模块，以及handoff/coverage gate模式。

## 内容边界

- 方法名称、示例和主要用途来自用户PDF。
- 本Skill增加的统计限制、审计字段、分层规则和脚本属于结构化设计增强。
- PDF中部分“按显著性寻找设定”的表述被保留在来源记录中，但不会被写成自动执行规则。
