"""Compare the actual streetside façade and roof on the signed 244 and 245 city sites."""
import sys,os,json,subprocess,time,hashlib,fcntl,shutil
from datetime import datetime,timezone
from pathlib import Path
app=Path(__file__).resolve().parent
city=Path('/tmp/shanghai-main-245/final-map-31245')
out=Path('/dev/shm/grace245-city/same-street-cameras')
out.mkdir(exist_ok=True)
bank=Path('/dev/shm/city-245-actual')
case=Path('/workspace/e-resource/projects/shanghai/data/audit/meilun-west-nanjing-corner-v1/map-case.json')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
ns={'__file__':str(city/'sequence.py')};sys.path.insert(0,str(city))
exec((city/'sequence.py').read_text().split("with (w/'runner.lock')")[0],ns)
dri=app/'same-two-cameras.cjs';assert sha(dri)=='34a5f60b8c7c366dea2053722bbeaa560f1923a3b02743f7cbe7a90556540128'
check=read(city/'bound-inputs.json');gate=Path(sys.argv[1]);g=read(gate)
assert g['all_children_exited'] and not g['remaining_children'] and g['host_sha256']==sha(city/'standalone/process.json')
with (out/'single.lock').open('a') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 for n,phase,report in ((244,'before','control-browser.json'),(245,'street','main-browser.json')):
  work=out/str(n);work.mkdir(exist_ok=True);prior_report=city/phase/report;prior_exit=city/phase/'process.json';prior=read(prior_exit)
  assert prior['exit_code']==0 and not prior['remaining_children'] and prior['report_sha256']==sha(prior_report)
  closed=work/'closed.json'
  if closed.is_file():
   old=read(closed);assert old['exit_code']==0 and old['report_sha256']==sha(work/report) and old['all_children_exited'];continue
  temp=out/('profile-'+str(n));temp.mkdir(exist_ok=True)
  env=dict(os.environ,SHANGHAI_PROJECT_ROOT=str(bank/'245'),QA_CONTROL_CATALOG=str(bank/'244/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=check['244']['catalog_sha256'],QA_CONTROL_CITY_COUNT='279',MODEL_BASE_URL=check[str(n)]['origin'],QA_CDP_PORT='19445',QA_OUTPUT_DIR=str(work),TMPDIR=str(temp),NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules')
  args=['node',dri,case,phase]+(['--control'] if n==244 else [])
  with (work/'browser.log').open('wb') as s:
   start=now();child=subprocess.Popen(args,env=env,stdout=s,stderr=subprocess.STDOUT,start_new_session=True);seen={}
   while child.poll() is None:seen.update(ns['sample_processes'](child.pid));time.sleep(.3)
  chromes={pid:v for pid,v in seen.items() if v[1] in ('chromium','chrome')};remaining=ns['remaining_processes'](seen)
  rr=work/report;code=child.returncode
  record=dict(order=245,source_order=n,parent_source=str(gate),parent_sha256=sha(gate),original_host_sha256=sha(prior_exit),original_report_sha256=sha(prior_report),started=start,finished=now(),phase=phase,node_pid=child.pid,node_closed=not Path('/proc',str(child.pid)).exists(),chromium_pids=sorted(chromes),remaining_children=remaining,remaining_chromium=sorted(set(remaining)&set(chromes)),all_children_exited=not remaining,exit_code=code,report=report,report_sha256=sha(rr) if rr.exists()else None)
  write(closed,record);assert code==0 and chromes and not remaining and record['node_closed']
  data=read(rr);assert data['completed'] and [q['file'] for q in data['screenshots']]==['street-from-nanjing.png','roof-from-nanjing.png'] and len(data['views'])==2
  assert data['catalog']['count']==n+35 and data['catalog']['sha256']==check[str(n)]['catalog_sha256']
  print(n,sha(closed),flush=True)
