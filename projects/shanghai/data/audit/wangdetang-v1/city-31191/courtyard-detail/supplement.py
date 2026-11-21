from pathlib import Path
from datetime import datetime,timezone
import hashlib, subprocess, json, os, sys,time
root=Path('/dev/shm/qa-wangdetang191-31');q=Path('/tmp/wangdetang191');p=Path('/workspace/e-resource/projects/shanghai')
while not (q/'191-map-slot-released.json').is_file():time.sleep(.5)
old=json.loads((q/'191-map-slot-released.json').read_bytes());assert old['exit']==0 and old['all_exited'] and not old['remaining_chromium']
profile=root/'extra-profile';profile.mkdir(exist_ok=True);out=root/'courtyard-detail';out.mkdir(exist_ok=True)
env={**os.environ,'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','MODEL_BASE_URL':'http://127.0.0.1:31191/','SHANGHAI_PROJECT_ROOT':str(root/'stage191'),'TMPDIR':str(profile),'QA_SEGMENT':'street','QA_OUTPUT_DIR':str(out),'MALLOC_ARENA_MAX':'2'}
with(out/'node.log').open('ab')as log:rc=subprocess.call(['node',root/'check-close.cjs',p/'data/audit/wangdetang-v1/map-case.json'],env=env,stdout=log,stderr=log)
live=[]
for f in Path('/proc').glob('[0-9]*/comm'):
 try:
  if f.read_text().strip()=='chromium' and str(profile).encode() in (f.parent/'cmdline').read_bytes() and (f.parent/'stat').read_text().rsplit(')',1)[1].split()[0]!='Z':live.append(int(f.parent.name))
 except OSError:pass
assert not live
doc=out/'main-browser.json';r=json.loads(doc.read_bytes());assert rc==0 and r['completed'] and not r['failed']and not r['errors']and len(r['screenshots'])==2,r.get('failure')
proof={'passed':True,'order':191,'exit':rc,'remaining_chromium':live,'finished':datetime.now(timezone.utc).isoformat(),'six_main_sessions_sha256':hashlib.sha256((q/'191-map-slot-released.json').read_bytes()).hexdigest(),'supplement_report':str(doc),'supplement_sha256':hashlib.sha256(doc.read_bytes()).hexdigest()}
f=q/'191-all-views-closed.json';part=f.with_suffix('.new');part.write_text(json.dumps(proof,indent=2)+'\n');part.replace(f)
