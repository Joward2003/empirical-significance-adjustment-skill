#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED = ['project_id','research_question','unit_of_observation','sample_period','outcome','core_exposure','baseline_specification','software']

def fail(msg: str) -> None:
    print(json.dumps({'valid': False, 'error': msg}, ensure_ascii=False))
    raise SystemExit(1)

def main(path: str) -> None:
    p=Path(path)
    if not p.exists(): fail(f'文件不存在: {p}')
    try: data=json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: fail(f'JSON解析失败: {e}')
    missing=[k for k in REQUIRED if k not in data]
    if missing: fail('缺少字段: '+', '.join(missing))
    sp=data['sample_period']
    if not isinstance(sp,dict) or 'start' not in sp or 'end' not in sp: fail('sample_period必须包含start和end')
    if sp['start']>sp['end']: fail('sample_period.start不能晚于end')
    bs=data['baseline_specification']
    for k in ['controls','fixed_effects','cluster']:
        if k not in bs or not isinstance(bs[k],list): fail(f'baseline_specification.{k}必须为数组')
    levels=data.get('allowed_adjustment_levels',['A','B','C'])
    bad=[x for x in levels if x not in ['A','B','C','D']]
    if bad: fail('未知调整等级: '+', '.join(bad))
    warnings=[]
    if not bs['cluster']: warnings.append('未指定聚类层级')
    if data['outcome'].get('has_zeros') and data['outcome'].get('type')=='continuous': warnings.append('连续因变量含零：检查对数/IHS处理')
    print(json.dumps({'valid': True,'project_id':data['project_id'],'warnings':warnings},ensure_ascii=False,indent=2))

if __name__=='__main__':
    if len(sys.argv)!=2: fail('用法: validate_project.py project.json')
    main(sys.argv[1])
