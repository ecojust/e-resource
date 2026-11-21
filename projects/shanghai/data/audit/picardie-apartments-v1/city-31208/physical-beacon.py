"""Exercise the map label from a previous landmark using separate real mouse and touchscreen sessions."""
from pathlib import Path
from process_family import chrome_descendants, still_alive
from datetime import datetime,timezone
import fcntl,json,os,sys,subprocess,tempfile,shutil,hashlib,time
q=Path(__file__).resolve().parent
p=Path('/workspace/e-resource/projects/shanghai');audit=p/'data/audit/picardie-apartments-v1'
read=lambda f:json.loads(f.read_bytes())
with(q/'physical-beacon.lock').open('a')as l:
 fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for old in read(q/'all-main-outcomes.json'):assert old['exit_code']==0 and not old['remaining_chromium']
 for mode in ('mouse','touch'):
  output=q/('physical-'+mode);output.mkdir(exist_ok=True);r=output/'physical-exit.json'
  if r.exists():assert read(r)['exit_code']==0;continue
  root=max([Path('/run/codex-docker/user'),Path('/dev/shm'),Path('/tmp')],key=lambda p:shutil.disk_usage(p).free)
  with tempfile.TemporaryDirectory(prefix='p8-',dir=root)as temp:
   env={**os.environ,'TMPDIR':temp,'QA_OUTPUT_DIR':str(output),'MODEL_BASE_URL':'http://127.0.0.1:31208/','SHANGHAI_PROJECT_ROOT':str(q/'208'),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
   begin=datetime.now(timezone.utc).isoformat()
   with(output/'browser.log').open('ab')as o:
    browser=subprocess.Popen(['node',q/'check-map-beacon.cjs',audit/'map-case.json',mode],env=env,stdout=o,stderr=o,start_new_session=True)
    seen={}
    while browser.poll() is None:
     seen.update(chrome_descendants(browser.pid))
     time.sleep(.23)
    rc=browser.returncode
   processes=[]
   for f in Path('/proc').glob('[0-9]*/cmdline'):
    try:parts=f.read_bytes().split(b'\0')
    except OSError:continue
    if b'chrom' in parts[0] and any(os.fsencode(temp)in s for s in parts):processes.append(int(f.parent.name))
   processes=sorted(set(processes)|set(still_alive(seen)))
   stopped=datetime.now(timezone.utc).isoformat()
   status={'kind':mode,'exit_code':rc,'pid':browser.pid,'remaining_chromium':processes,'observed_chromium_pid_and_starttime':seen,'started_utc':begin,'finished_utc':stopped}
   if rc or processes or not seen:
    report=output/'main-browser.json'
    if report.is_file():
     status.update(report=str(report),sha256=hashlib.sha256(report.read_bytes()).hexdigest())
    failed=output/'failed-process-exit.json'
    failed.write_text(json.dumps(status,indent=2)+'\n')
    raise RuntimeError(f'Physical {mode} browser failed. See {failed}.')
  file=output/'main-browser.json';report=read(file);sel,=report['physicalSelections'];assert report['completed'] and not report['errors'] and not report['failed'] and sel['input']==mode and sel['selected']=='xuhui-picardie-apartments-south-front'
  r.write_text(json.dumps({'kind':mode,'exit_code':rc,'pid':browser.pid,'remaining_chromium':processes,'observed_chromium_pid_and_starttime':seen,'started_utc':begin,'finished_utc':stopped,'report':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()},indent=2)+'\n')
