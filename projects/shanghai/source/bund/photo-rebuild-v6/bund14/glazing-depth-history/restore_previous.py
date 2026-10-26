#!/usr/bin/env python3
"""Restore exact pre-glazing building inputs into a new independent sibling layout."""
from pathlib import Path
import argparse, hashlib, json, shutil
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Output must not exist; refusing to overwrite')
m=json.loads((HERE/'baseline-source.json').read_text()); current=HERE.parent; common=current.parent/'common'; planned=[]
for row in m['files']:
 rel=Path(row['file'])
 if rel.is_absolute() or '..' in rel.parts:raise SystemExit('Invalid relative path')
 candidates=[current/rel,HERE/row['snapshot']] if row.get('snapshot') else [current/rel]
 src=next((q for q in candidates if q.is_file() and hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']),None)
 if src is None:raise SystemExit('Missing exact historical input: '+str(rel))
 planned.append((src,Path(m['id'])/rel,row['sha256']))
for row in m['common_files']:
 rel=Path(row['file']);src=common/rel
 if rel.is_absolute() or '..' in rel.parts or not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=row['sha256']:raise SystemExit('Common dependency mismatch: '+str(rel))
 planned.append((src,Path('common')/rel,row['sha256']))
for src,rel,expected in planned:
 target=a.output/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
 if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:raise SystemExit('Copy verification failed: '+str(rel))
print(json.dumps({'passed':True,'id':m['id'],'verified_files':len(planned),'output':str(a.output),'historical_raw_sha256':m['raw_sha256'],'scope':'Exact source inputs restored; model is not rebuilt by this utility.'}))
