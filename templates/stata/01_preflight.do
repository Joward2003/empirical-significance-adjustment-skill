* METHOD: A-level data preflight
isid $PANEL_ID $TIME
duplicates report $PANEL_ID $TIME
misstable summarize $Y $X $CONTROLS
xtdescribe
summarize $Y $X $CONTROLS, detail

* 检查处理状态是否反复变化（按项目改变量名）
* bysort $PANEL_ID ($TIME): assert treatment >= treatment[_n-1] if _n>1

* 不要在发现重复值后直接duplicates drop；先定位产生原因。

* 仅在以上检查通过后声明面板；若年份不连续，滞后变量须单独处理。
xtset $PANEL_ID $TIME
