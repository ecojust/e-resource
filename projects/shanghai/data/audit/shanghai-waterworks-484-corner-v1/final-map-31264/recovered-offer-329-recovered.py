"""Give one genuinely exited map session to the Cathay Apartments author and validate its return."""
from pathlib import Path
import json, hashlib, subprocess, sys, os
q=Path('/tmp/shanghai-main-264');w=Path('/tmp/cathay329')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def rd(f):return json.loads(f.read_bytes())
kind=sys.argv[1];source=Path(os.path.abspath(sys.argv[2]));assert source.is_file()
guest=rd(q/'guest-329-recovered.json');dispatch=Path(guest['dispatch']);program=Path(guest['admission'])
assert sha(dispatch)==guest['dispatch_sha256'] and sha(program)==guest['admission_sha256']
closed=w/(kind+'-closed.json')
if closed.is_file():
    earlier=rd(closed);current=rd(source)
    assert earlier['order']==329 and earlier['host']==264 and earlier['kind']==kind
    assert earlier['passed'] and earlier['exit']==0 and earlier['all_processes_closed'] and not earlier['remaining']
    assert earlier['host_receipt_sha256']==sha(source) and earlier['host_report_sha256']==current['report_sha256']==sha(Path(current['report']))
    if kind=='native':
        assets=Path('/workspace/e-resource/projects/shanghai/assets/models/candidates/huangpu-cathay-apartments-east-window-bay')
        assert len(earlier['assets'])==4 and sha(assets/'manifest.json')==earlier['manifest_sha256']
        assert all(sha(assets/x['file'])==x['sha256'] for x in earlier['assets'].values())
        assert len(earlier['blender_pids'])>=2 and all(x['exit']==0 for x in earlier['native_stages'])
    else:
        assert earlier['dispatch_sha256']==sha(dispatch) and sha(Path(earlier['report']))==earlier['report_sha256']
        assert len(earlier['saved_files'])==4 and all(sha(Path(x['path']))==x['sha256'] for x in earlier['saved_files'].values())
else:
    subprocess.run([sys.executable,'-Bu',program,kind,source],check=True)
tickets=[x for x in (w/(kind+'-closed.json'),w/('264-'+kind+'-deferred.json'),w/('264-'+kind+'-failed.json'))if x.is_file()]
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
(q/('329-'+kind+'-result.json')).write_text(json.dumps(dict(host=264,order=329,source=str(source),source_sha256=sha(source),report_sha256=h['report_sha256'],result=str(t),result_sha256=sha(t)),indent=2)+'\n')
