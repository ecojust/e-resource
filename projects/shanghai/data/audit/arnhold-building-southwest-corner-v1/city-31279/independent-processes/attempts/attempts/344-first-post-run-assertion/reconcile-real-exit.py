"""Verify the completed two-device visit against the frozen launching program and both actual process families."""
from pathlib import Path
import ast,hashlib,json,sys,subprocess,re,datetime
w=Path('/tmp/guangci344');a=Path(sys.argv[1]);h=Path('/tmp/shanghai-main-279')
read=lambda p:json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 data=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
 if p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
t=h/'evidence/phone/closed.json';c=read(w/'mapping/handoff/dispatch-live.json');g=w/'mapping/handoff';p=read(a/'processes.json')[0];v=read(a/'viewer.json');m=read(w/'issued-four/manifest.json')['assets']
for f,s in c['programs_and_inputs'].items():assert sha(Path(f))==s,f
assert sha(g/'dispatch-live.json')=='e3f4def220e751b06d2bcf79955236bc81b6323bf05a708d023247739fdbbf93'
assert p['exit']==0 and p['wrapper_closed'] and p['remaining']==[] and sha(a/'ordinary-viewer.log')==p['log_sha256']
src=(g/'run-344-devices.py').read_text();ast.parse(src)
assert "cmd=['node','-r'," in src and "run=subprocess.Popen(cmd,stdout=log,stderr=log,env=env);run.wait()" in src and 'node=run.pid' in src
node_ref=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify({name:require('fs').readFileSync('/proc/self/comm','utf8').trim(),version:process.version}))"]))
assert node_ref['name'] in {'node','MainThread'}
states=[];browser=[]
for unit in ('desktop','mobile'):
 q=read(a/(unit+'-node-exit.json'));r=read(a/(unit+'-viewer.json'));pid=q['node'];tree=p['children'][str(pid)];assert tree['parent']==p['pid'] and tree['name'] in {'node',node_ref['name']} and q['exit']==0 and q['report_sha256']==sha(a/(unit+'-viewer.json'))
 assert r['passed'] and r['closed'] and not r['pageErrors'] and r['device']==unit and r['scriptSHA256']==sha(g/'six-view-download-live.cjs')
 log=(a/(unit+'-node.log')).read_text();matches=re.findall(r'<launched> pid=(\d+)',log);assert len(matches)==1
 chrome=int(matches[0]);assert p['children'][str(chrome)]['parent']==pid and p['children'][str(chrome)]['name'] in {'chromium','chrome'} and f'[pid={chrome}] <process did exit: exitCode=0' in log
 browser.append(chrome);states.append(q)
assert states[0]['finished_ns']<states[1]['started_ns'] and len(set(browser))==2 and len({q['node']for q in states})==2
assert len(v['views'])==6 and set(v['downloads'])==set(m) and sha(a/'viewer.json')==sha(w/'standalone-31344/viewer.json')
for i in v['views']:assert sha(a/i['filename'])==i['sha256']==sha(w/'standalone-31344'/i['filename'])
for k,i in v['downloads'].items():
 f=a/i['saved'];assert sha(f)==i['sha256']==m[k]['sha256'] and f.stat().st_size==i['bytes'] and i['saveAsVerified']
parent=Path('/tmp/wanyi343/raw-343-confirmed.json')
receipt=dict(order=344,host=279,kind='viewer',host_receipt_sha256=sha(t),host_report_sha256=read(t)['report_sha256'],dispatch_sha256=sha(g/'dispatch-live.json'),parent_snapshot_sha256=read(parent)['sha256'],parent_receipt_sha256=sha(parent),passed=True,exit=0,exit_code=0,remaining=[],remaining_chromium=[],wrapper_closed=True,device_nodes=states,actual_directory=str(a),chromium_pids=browser,views=6,downloads=4,node=p['pid'],report=str(w/'standalone-31344/viewer.json'),receipt_sha256=sha(a/'viewer.json'),saved_files=str(a/'saved'),observed=[p],device_source_sha256=sha(g/'run-344-devices.py'),original_admission_sha256=sha(g/'admit-window-live.py'),first_wrapper_failure='Task finished with six screens and four saves. Outer original assertion required Linux comm=node for each Node parent and returned 1 upon reading MainThread.',first_wrapper_log_sha256=sha(Path('/dev/shm/arnhold279-live/host11.log')),reconciled_via='Both actual child PIDs, frozen Popen node launch, each device log and launched browser PID, both device exits and recorded Linux birth ticks',current_node_probe=node_ref,reconciliation_program_sha256=sha(Path(__file__)))
put(w/'viewer-closed.json',receipt);print(sha(w/'viewer-closed.json'),browser)
