#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, hashlib
from pathlib import Path
from datetime import datetime, timezone

def sha256(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    src=Path(args.project); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    project=json.loads(src.read_text(encoding='utf-8'))
    project_copy=out/'project.json'
    serialized=json.dumps(project,ensure_ascii=False,indent=2) + '\n'
    if project_copy.exists() and project_copy.read_text(encoding='utf-8') != serialized:
        raise SystemExit('运行目录已包含不同的project.json；请新建运行目录，避免覆盖审计配置。')
    if not project_copy.exists():
        project_copy.write_text(serialized,encoding='utf-8')
    snapshot={
      'created_at':datetime.now(timezone.utc).isoformat(),
      'project_sha256':sha256(src),
      'baseline_specification':project['baseline_specification'],
      'baseline_result':None,
      'locked':False
    }
    snap=out/'baseline_snapshot.json'
    if not snap.exists(): snap.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2) + '\n',encoding='utf-8')
    (out/'adjustment_log.jsonl').touch(exist_ok=True)
    print(json.dumps({'status':'initialized','out':str(out),'baseline_snapshot_created':True},ensure_ascii=False))
if __name__=='__main__': main()
