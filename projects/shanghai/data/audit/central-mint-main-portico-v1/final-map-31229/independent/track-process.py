from pathlib import Path
import datetime, fcntl, hashlib,json,os,psutil,subprocess,sys,time
w=Path(sys.argv[1])
def h(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
with Path('/tmp/shanghai-standalone-viewer.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);start=now();seen={};chrome={};peak=0;single=0
 with (w/'run.log').open('wb') as log:
  child=subprocess.Popen(sys.argv[2:],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'TMPDIR':str(w),'NODE_PATH':'/tmp/country-tools/node_modules'},start_new_session=True)
  host=psutil.Process(child.pid);seen[child.pid]=host.create_time()
  while child.poll() is None:
   try:
    subtotal=0
    for c in [host,*host.children(recursive=True)]:
     try:
      seen[c.pid]=c.create_time();rss=c.memory_info().rss;subtotal+=rss
      if 'chrom' in c.name():chrome[c.pid]=seen[c.pid];single=max(single,rss)
     except psutil.NoSuchProcess:pass
    peak=max(peak,subtotal)
   except psutil.NoSuchProcess:pass
   time.sleep(.08)
 def remains():
  arr=[]
  for k,b in seen.items():
   try:
    p=psutil.Process(k)
    if p.create_time()==b and p.status() not in (psutil.STATUS_DEAD,psutil.STATUS_ZOMBIE):arr.append(k)
   except psutil.NoSuchProcess:pass
  return arr
 for _ in range(50):
  if not remains():break
  time.sleep(.1)
 report=Path(os.environ['CAPTURED_REPORT']);alive=remains()
 data={'started':start,'finished':now(),'exit':child.returncode,'exit_code':child.returncode,'node_closed':not host.pid in alive,'node_pid':host.pid,'chromium_pids':list(chrome),'observed_pid_births':seen,'remaining_chromium':[k for k in alive if k in chrome],'remaining_children':alive,'all_children_exited':not alive,'report':str(report),'report_sha256':h(report) if report.exists() else None,'log_sha256':h(w/'run.log'),'sum_rss_sampled_bytes':peak,'largest_chromium_rss_bytes':single,'sample_period_seconds':.08,'driver_sha256':h(os.environ['CAPTURED_DRIVER'])}
 (w/'closed.json').write_text(json.dumps(data,indent=2)+'\n')
 assert not alive and chrome and child.returncode==0 and json.loads(report.read_bytes())['passed']
