"""Schedule the Kakuta arched-window development native and viewer in the confirmed 239th city final slot."""
from pathlib import Path
from hashlib import sha256
import json,sys,subprocess,os
host=Path(__file__).parent;city=host/'final-map-31239';q=Path('/tmp/minhang405/development-native')
def sha(f):
 with f.open('rb')as r:return __import__('hashlib').file_digest(r,'sha256').hexdigest()
def read(f):return json.loads(f.read_bytes())
def write(f,x):
 b=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
 if f.is_file():assert f.read_bytes()==b
 else:
  t=f.with_suffix('.new');t.write_bytes(b);t.replace(f)
source=city/'distant/process.json';stand=city/'standalone-closed.json';a=read(stand);s=read(source)
assert s['phase']=='distant'and s['node_closed']and s['exit_code']==0 and s['chromium_pids']and not(s['remaining_children']or s['remaining_chromium'])
rr=city/'distant/main-browser.json';assert sha(rr)==s['report_sha256']and read(rr)['completed']
sr=city/'standalone-31239/viewer.json';assert a['exit']==0 and a['chromium_pids'] and not(a['remaining_observed']or a['chromium_remaining']) and a['report_sha256']==sha(sr) and read(sr)['passed']
matrix=city/'all-real-processes-closed.json'
assert read(matrix)['phases']==7
sources={'city_closure':source,'city_report':rr,'standalone':stand,'standalone_report':sr,'all_sessions':matrix}
for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
 close=city/phase/'process.json';item=read(close);report=city/phase/('control-browser.json' if phase=='before' else 'main-browser.json')
 assert item['phase']==phase and item['exit_code']==0 and item['node_pids'] and item['chromium_pids'] and item['node_closed'] and not item['remaining_children'] and not item['remaining_chromium'] and item['report_sha256']==sha(report) and read(report)['completed']
 sources[phase+'_process']=close;sources[phase+'_report']=report
assert len(read(sr)['views'])==6 and len(read(sr)['downloads'])==4
prior_return=host/'401-development-returned.json'
first=read(prior_return)
assert first['host']==239 and first['order']==401 and first['all_children_exited'] and not first['remaining_children']
assert first['physical_sha256']==sha(Path(first['physical'])) and read(Path(first['physical']))['exit_code']==first['exit_code']
sources['previous_development_return']=prior_return
sources['previous_development_physical']=Path(first['physical'])
w=host/'405-prior-closed.json';write(w,dict(order=239,all_children_exited=True,remaining_children=[],sources={n:{'file':str(f),'sha256':sha(f)}for n,f in sources.items()}))
exe=q/'start.py';author=Path('/workspace/e-resource/projects/shanghai/data/audit/kakuta-apartments-corner-arched-windows-v1/preflight/model-review.json')
assert sha(exe)=='22dbd7aee25825c01b467f8ab8d13ff01e9335e66107586493052e0165639cb4' and sha(author)=='67906fce0875763c3eab4d0c466c096bebd7ad032d14b104a23f5d4e0a489768'
rc=subprocess.run([sys.executable,'-Bu',exe,w,sha(author)]).returncode
physical=q/'physical.json';v=read(physical);assert v['exit_code']==rc and v['all_children_exited'] and not v['remaining_children']
write(host/'405-development-returned.json',dict(order=405,host=239,prior_sha256=sha(w),physical=str(physical),physical_sha256=sha(physical),passed=not rc,exit_code=rc,all_children_exited=True,remaining_children=[]))
