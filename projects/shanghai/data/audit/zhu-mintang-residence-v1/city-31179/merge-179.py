"""Reconcile the separately closed city sessions and keep the interrupted full run for comparison."""
import hashlib
import json
import os
import shutil
from pathlib import Path

work=Path(__file__).parent
home=work/'evidence/179'
sources=home/'separate'
target=home/'after'
output=Path('/workspace/e-resource/projects/shanghai/data/audit/zhu-mintang-residence-v1/city-31179')
parts=['desktop','phone','details','distant','viewer']
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():
  try:os.link(src,dst)
  except OSError:shutil.copyfile(src,dst)
 assert sha(src)==sha(dst)
clean={};receipts={}
for part in parts:
 row=read(sources/part/'after.json');c=read(sources/part/'closed.json')
 assert row['completed'] and row['browserClosed'] and row['section']==part
 assert c['node_closed'] and not c['remaining'] and c['chromium_pids'] and c['exit']==0
 assert c['report_sha256']==sha(sources/part/'after.json') and c['driver_sha256']==row['scriptSha256']==sha(work/('check-179-distant-direct.cjs'if part in ('viewer','distant')else'check-179-separated.cjs'))
 assert all(not row.get(k)for k in ('failedRequests','httpErrors','pageErrors','failure'))
 clean[part]=row;receipts[part]=c
for field in ('beforeReceipt','catalog','caseSha256','contractSha256','groundSha256','snapshotSha256','nativeInputs','modelInputs','files'):
 assert all(clean[p][field]==clean['desktop'][field]for p in parts),field
assert len(clean['details']['ground'])==24 and len(clean['details']['sources'])==2
assert {v['device']for p in parts for v in clean[p]['actions']}=={'desktop','phone'}
assert len(clean['viewer']['downloads'])==4
views=[v for p in parts for v in clean[p]['views']]
assert len({v['file']for v in views})==6
target.mkdir(exist_ok=True)
for part in parts:
 for image in clean[part]['views']:
  f=sources/part/image['file'];assert sha(f)==image['sha256'];copy(f,target/f.name)
 copy(sources/part/'after.json',output/'sessions'/part/'after.json')
 copy(sources/part/'closed.json',output/'sessions'/part/'closed.json')
copy(work/'check-179-separated.cjs',output/'check-179-separated.cjs')
copy(Path(__file__),output/'merge-179.py')
copy(work/'check-179-distant-direct.cjs',output/'check-179-distant-direct.cjs')
copy(work/'split-179-far-direct.py',output/'split-179-far-direct.py')
for n in ['after.json','closed.json']:copy(home/'initial-distant-renderer-interruption'/n,output/'initial-distant-renderer-interruption'/n)
copy(work/'split-179.py',output/'split-179.py')
copy(home/'initial-after-renderer-interruption/after.json',output/'initial-after-renderer-interruption/after.json')
copy(home/'initial-after-renderer-interruption/exit.json',output/'initial-after-renderer-interruption/exit.json')
copy(home/'initial-after-renderer-interruption/map-desktop.png',output/'initial-after-renderer-interruption/map-desktop.png')
merged=dict(clean['details'])
merged.pop('section',None)
merged['actions']=[a for p in parts for a in clean[p]['actions']]
merged['views']=views
merged['downloads']=clean['viewer']['downloads']
merged['sessions']=receipts
merged['pageResponses']={k:v for p in parts for k,v in clean[p].get('pageResponses',{}).items()}
merged['started']=min(row['started']for row in clean.values());merged['finished']=max(row['finished']for row in clean.values())
merged['capture_method']='Archive of five complete real browser runs, with individual reports and process exits in sessions/.'
save(target/'after.json',merged)
save(target/'exit.json',{'code':0,'phase':'after','base':merged['site'],'production':sha(work/'179-production.json'),'driver_sha256':merged['scriptSha256'],'case_sha256':merged['caseSha256'],'finished':merged['finished'],'sessions':receipts})
