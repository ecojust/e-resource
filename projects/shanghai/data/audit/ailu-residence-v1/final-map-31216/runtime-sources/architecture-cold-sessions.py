"""Run one genuinely separate Node/Chrome instance for each architectural photograph."""
from pathlib import Path
import ast, hashlib, json, os, shutil, subprocess, sys, time
w=Path('/tmp/shanghai-main-216/final-map-31216')
out=Path(os.environ['QA_OUTPUT_DIR']);case=Path(sys.argv[1]);driver=w/'check-map-stages.cjs'
static_sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');temp.replace(p)
def read(p):return json.loads(p.read_bytes())
namespace={'P':Path}
tree=ast.parse((w/'sequence.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('sample_processes','remaining_processes')],type_ignores=[]),'sequence-physical-definitions','exec'),namespace)
stems=['map-desktop-panel-collapsed','map-street-facade','map-roof','map-arch-and-railing','map-gallery-and-dormer']
files=[];reports=[];pids=[]
for stem in stems:
 driver=w/('architecture-gallery-camera.cjs' if stem=='map-gallery-and-dormer' else 'check-map-stages.cjs')
 folder=out/'sessions'/stem;folder.mkdir(parents=True,exist_ok=True);procfile=folder/'process.json';rep=folder/'main-browser.json'
 if not procfile.exists():
  assert not rep.exists(),folder
  with (folder/'node.log').open('wb')as log:
   child=subprocess.Popen(['node',driver,case,'architecture'],env={**os.environ,'QA_ARCH_SHOT':stem,'QA_OUTPUT_DIR':str(folder)},stdout=log,stderr=subprocess.STDOUT)
   seen={}
   while child.poll() is None:seen.update(namespace['sample_processes'](child.pid));time.sleep(.45)
  nodes={p:v for p,v in seen.items() if v[1] in ('MainThread','node','nodejs')};chromes={p:v for p,v in seen.items() if v[1] in ('chrome','chromium')}
  state=dict(stem=stem,node_pid=child.pid,node_pids=sorted(nodes),chromium_pids=sorted(chromes),remaining_children=namespace['remaining_processes'](nodes|chromes),exit_code=child.returncode,report_sha256=static_sha(rep) if rep.is_file() else None,log_sha256=static_sha(folder/'node.log'))
  write(procfile,state)
 state=read(procfile);assert state['exit_code']==0 and state['node_pids'] and state['chromium_pids'] and not state['remaining_children'] and state['report_sha256']==static_sha(rep),state
 r=read(rep);assert r['completed'] and r['phase']=='architecture' and r['server']=='http://127.0.0.1:31216/' and r['scriptSha256']==static_sha(driver) and not r['errors'] and not r['failed'] and r['ground']
 name=stem+'.png';s,=r['screenshots'];assert s['file']==name and static_sha(folder/name)==s['sha256']
 if not (out/name).exists():os.link(folder/name,out/name)
 assert static_sha(out/name)==s['sha256'];reports.append(r);pids.append(dict(path=str(procfile),sha256=static_sha(procfile),driver=str(driver),driver_sha256=static_sha(driver)))
 print(stem,state['exit_code'],s['sha256'],flush=True)
base=reports[0].copy()
for key in ('id','mode','server','caseSha256','catalog','bindings','ground','sourceCommit'):
 assert all(r[key]==base[key] for r in reports),key
base['driverScope']='The first camera identifies the common capture implementation. physical_camera_sessions identifies the exact executed driver for every camera.'
base.update(views=[v for r in reports for v in r['views']],screenshots=[s for r in reports for s in r['screenshots']],architecturalPixels=[a for r in reports for a in r.get('architecturalPixels',[])],finished=reports[-1]['finished'],physical_camera_sessions=pids)
write(out/'main-browser.json',base)
