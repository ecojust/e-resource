"""Run the scheduled editing or standalone window after its preceding browser has closed."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,time
w=Path(__file__).parent
phase=sys.argv[1]
if phase=='before':
    mark=w.parent/'255-native-window.json';success=Path('/tmp/hardoon255/native-slot-released.json')
    report=w/'before/before.json'
elif phase=='desktop':
    mark=Path('/tmp/siming254/standalone-window.json');success=Path('/tmp/siming254/standalone-closed.json')
    report=w/'desktop/after.json'
elif phase=='phone':
    mark=w.parent/'255-viewer-window.json';success=Path('/tmp/hardoon255/viewer-slot-released.json')
    report=w/'phone/after.json'
else:raise ValueError(phase)
def read(path):return json.loads(path.read_bytes())
assert (w/(phase+'.exit')).read_text().strip()=='0' and report.exists()
r=read(report)
assert r.get('browserClosed') and r.get('completed'),r.keys()
for file in Path('/proc').glob('[0-9]*/comm'):
    try:
        name=file.read_text().strip()
        if name not in ['chromium','chrome']:continue
        if (file.parent/'stat').read_text().rsplit(')',1)[1].split()[0]=='Z':continue
        args=(file.parent/'cmdline').read_bytes()
        assert b'/tmp/yan816188' not in args,(file,args)
    except OSError:pass
if not mark.exists():
    receipt=dict(order=188,phase=phase,exit=0,remaining_chromium=[],report=str(report),
      sha256=hashlib.sha256(report.read_bytes()).hexdigest(),closed_at=datetime.now(timezone.utc).isoformat())
    tmp=mark.with_suffix('.new');tmp.write_text(json.dumps(receipt,indent=2)+'\n');tmp.replace(mark)
while not success.exists():time.sleep(3)
ticket=read(success)
assert ticket.get('exit',ticket.get('exit_code',ticket.get('returncode',0)))==0 and ticket.get('passed',True)
if phase=='before':assert ticket['order']==255 and ticket['wrapper_closed'] and ticket['remaining']==[]
