"""Capture the riverfront and its roof at full canvas resolution once the map downloads finish."""
import datetime,fcntl,hashlib,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
p=Path(__file__).parent
e=p/'evidence/193';dst=e/'river-photographs';dst.mkdir(exist_ok=True)
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
with (p/'supplement.lock').open('a')as gate:
 fcntl.flock(gate,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not (e/'separate/downloads/closed.json').is_file():time.sleep(2)
 d=read(e/'separate/downloads/closed.json');assert d['exit']==0 and d['node_closed'] and not d['remaining']
 with (p/'browser.lock').open('a')as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
  fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(light,fcntl.LOCK_EX)
  assert not (dst/'closed.json').exists()
  started=datetime.datetime.now(datetime.timezone.utc).isoformat();seen=set()
  fsroot=max(['/tmp','/dev/shm'],key=lambda k:shutil.disk_usage(k).free)
  with tempfile.TemporaryDirectory(prefix='river-photograph-',dir=fsroot)as tmp,(dst/'run.log').open('a')as log:
   env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','TMPDIR':tmp,'RIVER_FRAME_DIR':str(dst)}
   proc=subprocess.Popen(['node',p/'river-photographs.cjs'],env=env,stdout=log,stderr=log)
   while proc.poll()is None:
    for cmd in Path('/proc').glob('[0-9]*/cmdline'):
     try:argv=cmd.read_bytes().split(b'\0')
     except OSError:continue
     if argv and os.path.basename(argv[0])in (b'chrome',b'chromium',b'headless_shell')and (b'--remote-debugging-port=19694' in argv or any(v.startswith(os.fsencode('--user-data-dir='+tmp+'/'))for v in argv)):seen.add(int(cmd.parent.name))
    time.sleep(.9)
  active=[]
  for pid in seen:
   stat=Path('/proc')/str(pid)/'stat'
   if stat.is_file() and stat.read_text().rsplit(')',1)[1].split()[0]not in ('Z','X'):active.append(pid)
  rec=dst/'production-canvas.json'
  closed=dict(exit=proc.returncode,node=proc.pid,node_closed=not Path(f'/proc/{proc.pid}').exists(),remaining=active,chromium_pids=sorted(seen),started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=sha(p/'river-photographs.cjs'),report_sha256=sha(rec) if rec.is_file() else None)
  (dst/'closed.json').write_text(json.dumps(closed,indent=2)+'\n')
  assert closed['exit']==0 and closed['node_closed'] and seen and not active
  results=read(rec);assert results['completed'] and len(results['frames'])==2 and not results['errors']
  for shot in results['frames']:assert sha(dst/shot['file'])==shot['sha256']
  print('Actual canvas photos ready',flush=True)
