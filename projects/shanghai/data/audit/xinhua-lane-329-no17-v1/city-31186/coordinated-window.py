"""Confirm the closed segment and resume after the explicitly allocated 253 render window."""
from datetime import datetime,timezone
from pathlib import Path
from hashlib import sha256
import json,socket,sys,time
here=Path(__file__).parent;phase=sys.argv[1];assert phase in ['control','mobile'];e=here/'evidence';report=e/phase/('control-browser.json'if phase=='control'else'main-browser.json')
assert (e/(phase+'-exit')).read_text().strip()=='0';r=json.loads(report.read_bytes());assert r['completed'] and not(r['failed']or r['warnings']or r['errors'])
with socket.socket()as s:assert s.connect_ex(('127.0.0.1',19386))!=0
def h(f):return sha256(f.read_bytes()).hexdigest()
closed=dict(phase=phase,report=str(report),report_sha256=h(report),submitted_node_exit=0,remote_debugging_port_closed=19386,screenshots=[x['sha256']for x in r['screenshots']],utc=datetime.now(timezone.utc).isoformat())
path=e/(phase+'-stage-closed.json');assert not path.exists();path.write_text(json.dumps(closed,indent=2)+'\n')
decision=e/(phase+'-resume.json')
while not decision.exists():time.sleep(1)
resume=json.loads(decision.read_bytes());assert resume['phase_receipt_sha256']==h(path)
if resume['action']=='after-native':
 receipt=Path(resume['native_exit']);actual=json.loads(receipt.read_bytes());assert h(receipt)==resume['native_exit_sha256'] and (actual.get('exit')==0 or actual.get('exit_code')==0 or actual.get('returncode')==0)
else:assert resume['action']=='continue'
