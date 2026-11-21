"""Run each signed Shanghai facade placement from a fresh Chrome and retain every physical report."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
w=Path(__file__).parent
prior=Path(sys.argv[1]);stage=sys.argv[2];parent=w/'evidence/224/separate'/stage
views={'architecture':{'street':'map-street-facade','roof':'map-roof'},'closeups':{'arches':'map-beijing-road-shop-arches','oculi':'map-chamfer-and-two-oculi'}}[stage]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 tmp=p.with_suffix('.materializing');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
if (parent/'closed.json').is_file():
 assert load(parent/'closed.json')['report_sha256']==sha(parent/'main-browser.json') and load(parent/'main-browser.json')['completed'];sys.exit(0)
evidence={};reports=[];screens=[];scenes=[];files=[];ground=[];nodes=[];chromes=[];started=[];finished=[]
for component,view in views.items():
 folder=parent/'components'/component
 subprocess.run([sys.executable,'-Bu',w/'run-224-separated.py',prior,stage],check=True,env={**os.environ,'QA224_FOCUS':component})
 report=folder/'main-browser.json';returned=folder/'closed.json';drv=folder/'driver.cjs'
 r=load(report);c=load(returned)
 assert r['completed'] and not r.get('failure') and not r['errors'] and not r['failed'] and r['focus']==component and r['section']==stage
 assert [v['view'] for v in r['views']]==[view] and [s['file'] for s in r['screenshots']]==[view+'.png']
 assert c['report_sha256']==sha(report) and c['driver_sha256']==r['scriptSha256']==sha(drv) and c['exit']==0 and c['node_closed'] and c['chromium_pids'] and c['remaining']==[]
 assert sha(folder/(view+'.png'))==r['screenshots'][0]['sha256'];dst=parent/(view+'.png')
 if not dst.exists():os.link(folder/(view+'.png'),dst)
 assert sha(dst)==r['screenshots'][0]['sha256']
 evidence[component]=dict(report=report.relative_to(parent).as_posix(),report_sha256=sha(report),closed=returned.relative_to(parent).as_posix(),closed_sha256=sha(returned),driver_sha256=sha(drv))
 nodes.append(c['node']);chromes.extend(c['chromium_pids']);started.append(r['started']);finished.append(c['finished']);reports.append(r)
 screens.extend(r['screenshots']);scenes.extend(r['views']);files.extend(r['files']);ground.extend(r.get('ground',[]))
if stage=='architecture':assert len(ground)==29 and all(x['found']==x['expected']for x in ground)
assert len(chromes)==len(set(chromes)) and len(nodes)==len(set(nodes))
joined=dict(reports[0]);joined.pop('focus')
keys=['catalog','id','caseSha256','scriptSha256','bindings','server'];assert all(all(r[k]==joined[k] for k in keys) for r in reports)
seen={}
for item in files:
 path=item['file'];old=seen.get(path,item);assert (old['sha256'],old['bytes'])==(item['sha256'],item['bytes']);seen[path]={**item,'loadedByScene':item['loadedByScene'] or old['loadedByScene']}
joined.update(started=min(started),finished=max(finished),views=scenes,screenshots=screens,files=list(seen.values()),components=evidence)
if ground:joined['ground']=ground
save(parent/'main-browser.json',joined);(parent/'driver.cjs').write_bytes((parent/'components'/next(iter(views))/'driver.cjs').read_bytes())
save(parent/'closed.json',dict(exit=0,node=nodes[-1],node_pids=nodes,chromium_pids=chromes,node_closed=True,remaining=[],report_sha256=sha(parent/'main-browser.json'),driver_sha256=sha(parent/'driver.cjs'),components=evidence,finished=max(finished)))
