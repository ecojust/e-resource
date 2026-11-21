"""Reconcile the real page, retained exit status and two independently observed live processes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,psutil,urllib.request
w=Path(__file__).parent;d=w/'phone';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((d/'main-browser.json').read_bytes());assert r['completed'] and 'finished'in r and r['server']=='http://127.0.0.1:31212/' and not r['failed'] and not r['errors']
assert (w/'phone.exit').read_text().strip()=='0'
assert sorted(x['file']for x in r['screenshots'])==['map-mobile-settled.png','map-mobile.png']
for x in r['screenshots']:assert h(d/x['file'])==x['sha256'] and (d/x['file']).stat().st_size==x['bytes']
observed={'node':1343001,'chromium':1343096};current={}
for name,pid in observed.items():
 try:v=psutil.Process(pid);current[name]=dict(pid=pid,state=v.status(),born=v.create_time())
 except psutil.NoSuchProcess:current[name]=dict(pid=pid,state='absent')
 assert current[name]['state'] in ('absent','zombie')
matches=[]
for p in psutil.process_iter(['pid','cmdline','status']):
 argv=p.info['cmdline']or []
 if p.info['status']=='zombie':continue
 if argv and ('chrom' in Path(argv[0]).name or Path(argv[0]).name=='node') and any('profile-phone' in z or '--remote-debugging-port=19412'==z or z==str(w/'check-map-stages.cjs')for z in argv):matches.append(p.pid)
assert not matches,matches
try:urllib.request.urlopen('http://127.0.0.1:19412/json/version',timeout=1)
except OSError:pass
else:raise RuntimeError('The browser debugging endpoint is still live')
p=Path('/proc/1342918/stat');watchstate=p.read_text().rsplit(')',1)[1].split();assert watchstate[0]=='Z' and watchstate[-1]=='9'
out=dict(phase='phone',exit_code=0,node_pids=[observed['node']],chromium_pids=[observed['chromium']],node_closed=True,remaining_children=matches,remaining_chromium=[],started=r['started'],finished=datetime.now(timezone.utc).isoformat(),report_sha256=h(d/'main-browser.json'),monitor_recovered=True,monitor_process={'pid':1342918,'state':'zombie','wait_status':9},observed_processes=current,actual_wrapper_exit_file=str(w/'phone.exit'),actual_wrapper_exit_sha256=h(w/'phone.exit'),observer_note='Node and Chromium observed live in process listing during the actual phone phase, CDP used on port 19412 for the separately recorded near zoom. Final report written after browser.close and real node status returned by run.py; observer killed before saving census. Listed PIDs are independently observed IDs, not a continuous census.',supplemental_zoom_sha256=h(d/'supplemental-zoom.json'))
(d/'process.json').write_text(json.dumps(out,indent=2)+'\n')
