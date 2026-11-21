from pathlib import Path
import fcntl,json,os,shutil,subprocess,tempfile,time,datetime
w=Path(__file__).parent;out=w/'public-desktop';dest=w/'public-desktop-closed.json';case=Path('/workspace/e-resource/projects/shanghai/data/audit/yueyang-road-145-residence-v1/map-case.json')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as light:
 fcntl.flock(light,fcntl.LOCK_EX)
 while not(w/'exit').exists():time.sleep(.4)
 assert (w/'exit').read_text().strip()=='0' and json.loads((w/'segments/distant-closed.json').read_bytes())['exit']==0
 out.mkdir(exist_ok=True);assert not(out/'main-browser.json').exists();td=max(['/tmp','/dev/shm'],key=lambda where:shutil.disk_usage(where).free)
 temp=Path(tempfile.mkdtemp(prefix='shanghai-yueyang168-public-',dir=td))
 env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=str(temp),SHANGHAI_PROJECT_ROOT=str(w/'city168'),QA_SEGMENT='public',QA_OUTPUT_DIR=str(out),QA_CDP_PORT='9868',MODEL_BASE_URL='http://127.0.0.1:31168/')
 start=now()
 with (w/'public-desktop.log').open('ab',buffering=0)as log:
  proc=subprocess.Popen(['node',w/'check-public-zoom.cjs',case],env=env,stdout=log,stderr=log,start_new_session=True);rc=proc.wait()
 def live():
  result=[]
  for f in Path('/proc').glob('[0-9]*/cmdline'):
   try:s=f.read_bytes()
   except OSError:continue
   if str(temp).encode()in s and b'chromium' in s:result.append(int(f.parent.name))
  return result
 for i in range(20):
  if not live():break
  time.sleep(.5)
 report=json.loads((out/'main-browser.json').read_bytes());c=dict(exit=rc,started=start,finished=now(),remaining_chromium=live(),node_pid=proc.pid,report=str(out/'main-browser.json'),passed=report['completed'])
 dest.write_text(json.dumps(c,indent=2)+'\n');assert rc==0 and not c['remaining_chromium'] and report['completed'],c
