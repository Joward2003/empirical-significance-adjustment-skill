* METHOD: baseline_firm_fe
* 先锁定基准，不要覆盖输出。
reghdfe $Y $X $CONTROLS, absorb($FE) vce(cluster $CLUSTER)
estimates store BASELINE

* 保存核心统计量（按需要扩展postfile）
scalar beta_base = _b[$X]
scalar se_base   = _se[$X]
scalar n_base    = e(N)
scalar p_base    = 2 * ttail(e(df_r), abs(beta_base / se_base))
scalar ci_low_base  = beta_base - invttail(e(df_r), 0.025) * se_base
scalar ci_high_base = beta_base + invttail(e(df_r), 0.025) * se_base

* 同时记录e(N_clust)、singleton、warning、Stata版本和本do-file哈希（如可用），
* 并将这些字段与完整命令写入baseline-result.json后再运行lock_baseline_result.py。
