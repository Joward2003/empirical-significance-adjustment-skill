* 此文件故意不预置可运行的“调显著”矩阵。
* 只有已经写入 adjustment plan、具备独立诊断证据并获批准的规格才能复制到这里。
* 每段均须：
*   1) 标注 method_id 和调整等级；
*   2) 说明诊断证据与理论依据；
*   3) 保持或显式记录样本、控制、固定效应和聚类变化；
*   4) 无论结果如何都写入 adjustment_log.jsonl。
*
* 合法示例（默认不执行；先替换方括号内容并完成批准）：
* METHOD: [method_id] | LEVEL: [A/B/C]
* RATIONALE: [与p值无关的诊断或理论依据]
* reghdfe $Y $X $CONTROLS [if/in qualifier], absorb($FE) vce(cluster $CLUSTER)
* estimates store [APPROVED_MODEL_NAME]
*
* 在全部已批准模型运行后，使用 esttab 明确列出 BASELINE 与所有模型；
* 不要只导出显著模型，也不要根据结果删去模型。
