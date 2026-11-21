"""Bind four actual handbacks to the second ordinary-page regression for 348."""
from pathlib import Path
from hashlib import file_digest
import json,subprocess,sys
w=Path(__file__).parent;previous=Path('/tmp/shanghai-main-217/217-map-slot-released.json')
cold=Path('/tmp/shanghai-private-overlay-deltas/closed-23-160-180/217-window-returned.json')
vector=Path('/tmp/shaoxing9-347/vector/after-217-returned.json');model=Path('/tmp/shaoxing9-347/mapping/217-model-closed.json')
early=Path('/tmp/shanghai-main-217/348-regression-returned.json')
def sha(p):
    with p.open('rb')as f:return file_digest(f,'sha256').hexdigest()
def r(p):return json.loads(p.read_bytes())
def save(p,value):
    text=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if p.exists():assert text==p.read_text()
    else:
        t=p.with_suffix('.new');t.write_text(text);t.replace(p)
assert r(previous)['passed'] and not r(previous).get('remaining_chromium')
assert r(cold)['remaining']==[] and r(vector)['host_report_sha256']==sha(cold)
assert r(model)['remaining']==[] and r(model)['previous_return_sha256']==sha(vector)
assert r(early)['all_children_exited'] and not r(early)['remaining_children']
gate=w/'348-regression-authorized.json';save(gate,dict(order=217,all_children_exited=True,remaining_children=[],physical_receipts={str(x):sha(x) for x in [previous,cold,vector,model,early]}))
prog=Path('/tmp/mingfu348-study/detail-camera-v2/run.py');assert sha(prog)=='633aee1cd004bf3ad1202087c12bf2be8b8b02a1eaafe69239f55d143672a2a6'
cert=prog.parent/'physical.json'
if not cert.is_file():
    child=subprocess.Popen([sys.executable,'-B',prog,gate],start_new_session=True)
    rc=child.wait()
    assert r(cert)['exit_code']==rc
row=r(cert);assert row['order']==348 and row['all_children_exited'] and row['remaining_children']==[] and row['previous_sha256']==sha(gate)
save(w/'348-regression-returned.json',dict(order=348,program=sha(prog),host_receipt_sha256=sha(gate),actual_return=str(cert),actual_sha256=sha(cert),exit_code=row['exit_code'],remaining=[]))
