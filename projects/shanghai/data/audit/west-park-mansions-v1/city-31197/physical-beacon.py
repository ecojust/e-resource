"""Exercise the map label from a previous landmark using separate real mouse and touchscreen sessions."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,json,os,sys,subprocess,tempfile,shutil,hashlib,time
q=Path(__file__).resolve().parent
p=Path('/workspace/e-resource/projects/shanghai');audit=p/'data/audit/west-park-mansions-v1'
read=lambda f:json.loads(f.read_bytes())
with(q/'physical-beacon.lock').open('a')as l:
 fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for old in read(q/'all-main-outcomes.json'):assert old['exit_code']==0 and not old['remaining_chromium']
 for mode in ('mouse','touch'):
  output=q/('physical-'+mode);output.mkdir(exist_ok=True);r=output/'physical-exit.json'
  if r.exists():assert read(r)['exit_code']==0;continue
  root=max([q,Path('/dev/shm')], key=lambda p:shutil.disk_usage(p).free)
  with tempfile.TemporaryDirectory(prefix='west-park-beacon-',dir=root)as temp:
   env={**os.environ,'TMPDIR':temp,'QA_OUTPUT_DIR':str(output),'MODEL_BASE_URL':'http://127.0.0.1:31197/','SHANGHAI_PROJECT_ROOT':str(q/'stage197/projects/shanghai'),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'}
   begin=datetime.now(timezone.utc).isoformat()
   with(output/'browser.log').open('ab')as o:
    browser=subprocess.Popen(['node',q/'check-map-beacon.cjs',audit/'map-case.json',mode],env=env,stdout=o,stderr=o,start_new_session=True)
    rc=browser.wait()
   processes=[]
   for f in Path('/proc').glob('[0-9]*/cmdline'):
    try:parts=f.read_bytes().split(b'\0')
    except OSError:continue
    if b'chrom' in parts[0] and any(os.fsencode(temp)in s for s in parts):processes.append(int(f.parent.name))
   assert rc==0 and not processes
  file=output/'main-browser.json';report=read(file);sel,=report['physicalSelections'];assert report['completed'] and not report['errors'] and not report['failed'] and sel['input']==mode and sel['selected']=='changning-west-park-mansions'
  r.write_text(json.dumps({'kind':mode,'exit_code':rc,'pid':browser.pid,'remaining_chromium':processes,'started_utc':begin,'finished_utc':datetime.now(timezone.utc).isoformat(),'report':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()},indent=2)+'\n')
