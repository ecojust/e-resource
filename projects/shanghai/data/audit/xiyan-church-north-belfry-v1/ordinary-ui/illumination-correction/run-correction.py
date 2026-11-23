"""Open each of the three gallery links and save the corrected source archive on each device."""
import os,sys,json,hashlib,fcntl,subprocess,threading,functools
from pathlib import Path
from datetime import datetime,timezone
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import time,psutil
from PIL import Image
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
here=Path(__file__).absolute().parent;cor=here.parent;w=cor.parent;site=here/'site';run=here/'physical';pub=here/'publication'
regname='data/audit/xiyan-church-north-belfry-v1/registration'
id='changning-xiyan-church-north-belfry';assets='assets/models/candidates/'+id
for folder in (site,run,pub,site/assets,site/'assets',site/regname):folder.mkdir(exist_ok=True,parents=True)
pack=w/'final/packaged';page='xiyan-church-north-belfry.html'
def link(src,dest):
 if not dest.exists():dest.symlink_to(src)
 assert dest.samefile(src)
for n in (page,'src','vendor','source','landmarks.html','assets/favicon.svg'):link((w/'site'/n),site/n)
for f in (cor/'registration').glob('*.jpg'):link(f,site/regname/f.name)
archive=next((cor/'new-archive').glob('*-source.zip'))
assert sha(archive)=='b7b309caa724b8840e4100381dfc53bd37f9378a8b66a872b7623d3a28c77f76'
m=json.loads((pack/'manifest.json').read_bytes());objects={**m['assets'],**m['interchange']}
orig=json.loads((w/'final/ordinary-publication/ordinary-ui/visual-review.json').read_bytes())
for k,v in objects.items():
 assert sha(pack/v['file'])==v['sha256']==orig['devices']['desktop']['downloads'][k]['sha256']==orig['devices']['phone']['downloads'][k]['sha256']
 link(pack/v['file'],site/assets/v['file'])
link(pack/'manifest.json',site/assets/'manifest.json');link(archive,site/assets/archive.name)
names=['four-station-models.jpg','winter-river-model.jpg','june-court-model.jpg']
expected={'page':sha(site/page),'images':[dict(path=regname+'/'+n,sha256=sha(site/regname/n),size=list(Image.open(site/regname/n).size))for n in names],'archive':dict(file=archive.name,sha256=sha(archive),bytes=archive.stat().st_size)}
write(here/'expectation.json',expected)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=site))
threading.Thread(target=http.serve_forever,daemon=True).start()
record={}
with open(os.environ['QA_SHARED_LOCK'],'a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 for device in ('desktop','phone'):
  base=run/device;base.mkdir(exist_ok=True)
  for n in range(1,9):
   dest=base/str(n);dest.mkdir(exist_ok=True);receipt=dest/'closed.json';report=dest/'report.json'
   if not receipt.exists():
    env=dict(os.environ,QA_DEVICE=device,QA_ORIGIN='http://127.0.0.1:'+str(http.server_port),QA_SITE=str(site),QA_EXPECTATION=str(here/'expectation.json'),QA_OUT=str(dest),CHROMIUM_PATH=str(w/'ordinary/chromium-one'))
    for var in ('TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_RUNTIME_DIR'):
     d=Path(os.environ['QA_SHORT_TEMP'])/device/str(n)/var.lower();d.mkdir(exist_ok=True,parents=True,mode=0o700);env[var]=str(d)
    with (dest/'run.log').open('wb')as log:
     p=subprocess.Popen(['node','--max-old-space-size=76',here/'check.cjs'],stdout=log,stderr=log,env=env);obs=set()
     while p.poll() is None:
      try:
       for child in psutil.Process(p.pid).children(recursive=True):
        if child.name()=='chromium':obs.add((child.pid,child.create_time()))
      except psutil.Error:pass
      time.sleep(.035)
    remaining=[]
    for pid,birth in obs:
     try:
      q=psutil.Process(pid)
      if q.create_time()==birth and q.status()!='zombie':remaining.append(pid)
     except psutil.Error:pass
    write(receipt,dict(node=p.pid,chrome_pids=[x[0]for x in sorted(obs)],remaining=remaining,exit=p.returncode,report_sha256=sha(report)if report.exists()else None))
   c=json.loads(receipt.read_bytes())
   if c['exit'] or not c['chrome_pids'] or c['remaining'] or not report.is_file():continue
   r=json.loads(report.read_bytes());assert r['passed'] and r['closed'] and c['report_sha256']==sha(report) and sha(dest/archive.name)==sha(archive)
   record[device]={'report':r,'physical':c,'closed_sha256':sha(receipt),'report_sha256':sha(report)}
   break
  else:raise SystemExit('No physical exit for '+device)
http.shutdown();http.server_close()
write(pub/'correction-receipt.json',dict(previous_ordinary_report_sha256=orig['report_sha256'],previous_visual_review_sha256=sha(w/'final/ordinary-publication/ordinary-ui/visual-review.json'),camera_sha256=orig['cameras_sha256'],seven_unchanged_models=objects,device_checks=record,lighting=sha(cor/'registration/registered-illumination-correction.json')))
for f in (here/'check.cjs',here/'run-correction.py',here/'expectation.json'):
 if not (pub/f.name).exists():os.link(f,pub/f.name)
rows=[dict(path='projects/shanghai/data/audit/xiyan-church-north-belfry-v1/ordinary-ui/illumination-correction/'+p.name,source=str(p),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(pub.iterdir())]
write(here/'browser-publication.json',rows);print(sha(here/'browser-publication.json'),sha(pub/'correction-receipt.json'))
