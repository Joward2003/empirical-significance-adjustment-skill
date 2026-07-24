version 18.0
clear all
set more off
set seed 20260724

* ===== 项目配置：请按数据修改 =====
global DATA      "data/analysis.dta"
global OUT       "output"
global PANEL_ID  "firm_id"
global TIME      "year"
global Y         "y"
global X         "x"
global CONTROLS  "size lev roa growth"
global FE        "$PANEL_ID industry#year"
global CLUSTER   "policy_city"

cap mkdir "$OUT"
log using "$OUT/run.log", replace text
use "$DATA", clear
xtset $PANEL_ID $TIME
