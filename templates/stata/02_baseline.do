* METHOD: baseline_firm_fe
* 先锁定基准，不要覆盖输出。
reghdfe $Y $X $CONTROLS, absorb($FE) vce(cluster $CLUSTER)
estimates store BASELINE

* 保存核心统计量（按需要扩展postfile）
scalar beta_base = _b[$X]
scalar se_base   = _se[$X]
scalar n_base    = e(N)
