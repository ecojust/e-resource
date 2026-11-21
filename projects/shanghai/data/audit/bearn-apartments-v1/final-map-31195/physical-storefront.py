"""Capture the street-shop glass outside the location card and verify every process closes."""
from pathlib import Path
import subprocess,os,sys,json,time,hashlib,datetime
w=Path(__file__).parent
ns={'__file__':str(w/'sequence.py')};exec((w/'sequence.py').read_text().split('with (w/')[0],ns)
closed=w/'clear-shopfront/process.json'
if closed.is_file():
 r=json.loads(closed.read_bytes());assert r['exit_code']==0 and r['node_closed'] and not r['remaining_chromium'];sys.exit(0)
proc=subprocess.Popen([sys.executable,'-B',w/'run-clear-shopfront.py'],start_new_session=True)
seen={};started=ns['now']()
while proc.poll() is None:
 seen.update(ns['sample_processes'](proc.pid));time.sleep(.6)
nodes={p:key for p,key in seen.items()if key[1] in ('node','MainThread','nodejs')};chrome={p:key for p,key in seen.items()if key[1] in ('chrome','chromium')}
remaining=ns['remaining_processes'](nodes);alive=ns['remaining_processes'](chrome)
report=w/'clear-shopfront/main-browser.json'
data=dict(phase='clear-shopfront',started=started,finished=ns['now'](),exit_code=proc.returncode,node_pids=sorted(nodes),chromium_pids=sorted(chrome),node_closed=bool(nodes) and not remaining,remaining_children=sorted(remaining+alive),remaining_chromium=alive,report_sha256=hashlib.sha256(report.read_bytes()).hexdigest()if report.is_file() else None)
closed.parent.mkdir(exist_ok=True);closed.write_text(json.dumps(data,indent=2)+'\n')
assert nodes and chrome and data['node_closed'] and proc.returncode==0 and not data['remaining_children'] and json.loads(report.read_bytes())['completed']
