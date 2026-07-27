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
capture confirm file "$OUT/run.log"
if !_rc {
    display as error "已有 $OUT/run.log；请使用新的输出目录，避免覆盖审计证据。"
    exit 602
}
log using "$OUT/run.log", text
use "$DATA", clear

* 先运行01_preflight.do确认面板键唯一、年份连续性和缺失处理；
* 通过后才在该文件末尾或02_baseline.do中执行：xtset $PANEL_ID $TIME
