from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json,sys
w=Path(__file__).parent;e=w/'evidence';phase=sys.argv[1];assert phase in ('control','mobile');f=e/(phase+'-stage-closed.json');old=json.loads(f.read_bytes());assert old['phase']==phase and old['submitted_node_exit']==0
h=lambda p:sha256(p.read_bytes()).hexdigest()
r=dict(phase=phase,phase_receipt_sha256=h(f),utc=datetime.now(timezone.utc).isoformat(),action='continue')
if len(sys.argv)>2:
 native=Path(sys.argv[2]);d=json.loads(native.read_bytes());assert (d.get('exit')==0 or d.get('exit_code')==0 or d.get('returncode')==0)
 r.update(action='after-native',native_exit=str(native),native_exit_sha256=h(native))
out=e/(phase+'-resume.json');assert not out.exists();t=out.with_suffix('.tmp');t.write_text(json.dumps(r,indent=2)+'\n');t.replace(out)
