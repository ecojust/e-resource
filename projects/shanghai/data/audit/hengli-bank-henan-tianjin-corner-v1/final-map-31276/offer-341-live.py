"""Give one genuinely exited map session to the Cathay Apartments author and validate its return."""
from pathlib import Path
import json, hashlib, subprocess, sys
q=Path('/tmp/shanghai-main-276');w=Path('/tmp/fuxing341')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def rd(f):return json.loads(f.read_bytes())
kind=sys.argv[1];source=Path(sys.argv[2]).resolve(strict=True)
guest=rd(q/'guest-341-live.json');dispatch=w/'mapping/handoff/dispatch-live.json';program=dispatch.parent/'admit-window-live.py'
assert sha(dispatch)==guest['dispatch_sha256'] and sha(program)==guest['admission_sha256']
subprocess.run([sys.executable,'-Bu',program,kind,source],check=True)
tickets=[x for x in (w/(kind+'-closed.json'),w/('276-'+kind+'-deferred.json'),w/('276-'+kind+'-failed.json'))if x.is_file()]
assert len(tickets)==1
t=tickets[0];x=rd(t);h=rd(source)
assert x['host_receipt_sha256']==sha(source) and x['host_report_sha256']==h['report_sha256']
if t.name.endswith('-closed.json'):
 assert x['passed'] and x['exit']==0 and not x['remaining'] and x['all_processes_closed']
 if kind=='viewer':assert x['views']==6 and x['downloads']==4 and x['remaining_chromium']==[] and sha(Path(x['report']))==x['report_sha256']
 else:assert x['remaining_blender']==[] and len(x['assets'])==4 and x['blender_pids']
elif 'failed' in t.name:
 assert x['attempted'] and x['started'] and x['exit']!=0 and x['remaining_children']==[] and sha(Path(x['launch_process']))==x['launch_process_sha256']
else:assert x['deferred'] and x['attempted']==False and x['started']==False and x['missing']
(q/('341-'+kind+'-result.json')).write_text(json.dumps(dict(host=276,order=341,source=str(source),source_sha256=sha(source),report_sha256=h['report_sha256'],result=str(t),result_sha256=sha(t)),indent=2)+'\n')
