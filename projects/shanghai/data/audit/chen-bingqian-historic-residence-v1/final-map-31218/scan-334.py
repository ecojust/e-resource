"""Measure source and new-mesh occlusion after the admitted studio guests have returned."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import file_digest
import json,subprocess,sys
w=Path(__file__).parent
work=Path('/tmp/kemi334');md=work/'pilot'
def sha(p):
    with p.open('rb')as f:return file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def now():return datetime.now(timezone.utc).isoformat()
ticket=w/'347-model-real-handoff.json';prev=read(ticket);assert sha(Path(prev['actual_return']))==prev['actual_sha256'] and not read(Path(prev['actual_return']))['remaining']
out=work/'218-angle-screen.json'
if out.is_file():
    row=read(out);assert row['host_sha256']==sha(ticket) and not row['remaining'];sys.exit(0)
program=md/'scan-parcels-and-original-model.mjs';lib=md/'self-visibility.mjs';log=md/'218-angle-screen.log'
with log.open('xb')as fp:
    start=now();child=subprocess.Popen(['node','--max-old-space-size=50',program],stdout=fp,stderr=subprocess.STDOUT,start_new_session=True);rc=child.wait()
left=[]
for st in Path('/proc').glob('[0-9]*/stat'):
    try:row=st.read_text().rsplit(')',1)[1].split()
    except FileNotFoundError:continue
    if row[0]not in ('Z','X') and int(row[3])==child.pid:left.append(int(st.parent.name))
assert not left
actual=md/'source-and-original-mesh-screen.json';record=dict(order=334,host=218,host_sha256=sha(ticket),started=start,ended=now(),pid=child.pid,exit_code=rc,remaining=left,log_sha256=sha(log),program_sha256=sha(program),mesh_cone_library_sha256=sha(lib))
if rc==0:
    row=read(actual);assert row['angles']==12240;record.update(geometry_sweep_sha256=sha(actual),strongest_double_screen=row['best_count'])
out.write_text(json.dumps(record,indent=2)+'\n')
