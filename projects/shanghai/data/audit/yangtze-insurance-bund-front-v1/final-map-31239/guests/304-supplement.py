"""Resume the actual 31304 viewer from its first 239 phone and an additional true unoccupied interval."""
import fcntl,hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
q=Path('/tmp/shanghai-main-239')
city=q/'final-map-31239'
w=Path('/tmp/soong304');h=w/'mapping/handoff'
scenes=Path('/tmp/shanghai-yongjia-porch/scenes')
def sha(f):
    with f.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(f):return json.loads(f.read_bytes())
def store(f,d):
    t=f.with_suffix('.pending');t.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');t.replace(f)
def finish(f):
    d=read(f);r=f.with_name('main-browser.json')
    assert d['exit_code']==0 and d['node_closed'] and d['chromium_pids'] and not d['remaining_children'] and not d['remaining_chromium']
    assert sha(r)==d['report_sha256'] and read(r)['completed']
    return sha(r)
def now():return datetime.now(timezone.utc).isoformat()
def main():
    src=Path(sys.argv[1]);rs=finish(src)
    phone=city/'phone/process.json';pr=finish(phone)
    original=q/'304-viewer-deferred.json'
    actual=w/'viewer-closed.json';full=scenes/'304-all-http.json'
    result=w/(src.parent.name+'-304-ordinary-result.json')
    if result.is_file():
        old=read(result);assert old['host_sha256']==sha(src)
        if old.get('passed'):assert old['physical_sha256']==sha(actual)
        return
    info=dict(order=304,host=239,host_sha256=sha(src),host_report_sha256=rs,original_phone_sha256=sha(phone),started=False,all_children_exited=True,remaining_children=[])
    if original.exists():
        d=read(original);assert d['deferred'] and not d['chromium_started'] and d['previous_session_sha256']==sha(phone)
        info['original_deferral_sha256']=sha(original)
    if not full.exists() or not read(full)['passed']:
        store(result,dict(**info,deferred=True,missing=str(full),at=now()));return
    sys.path.insert(0,str(h));import receipts as ck
    ck.frozen();ck.raw(w/'raw-304-confirmed.json',304);ck.native(w/'native-closed.json',304)
    ck.completed_viewer(ck.PRIOR/'viewer-closed.json',303)
    comp=scenes/'304-comparison.json'
    assert read(comp)['passed'] and read(comp)['production_receipt_sha256']==read(full)['production_receipt_sha256']
    if not actual.is_file():
        assert original.is_file()
        grant=q/'304-viewer-window.json'
        inputs=[ck.PRIOR/'native-closed.json',ck.PRIOR/'raw-303-confirmed.json',ck.PRIOR/'viewer-closed.json',w/'native-closed.json',w/'raw-304-confirmed.json',comp,full]
        if not grant.exists():
            store(grant,dict(order=304,mode='viewer',authorized=True,previous_session=str(phone),previous_session_sha256=sha(phone),previous_browser_report_sha256=pr,
                             original_deferred_sha256=sha(original),additional_window=str(src),additional_window_sha256=sha(src),additional_report_sha256=rs,inputs={str(f):sha(f)for f in inputs},checked=now()))
        else:assert read(grant)['previous_session_sha256']==sha(phone)
        proc=subprocess.Popen([sys.executable,'-Bu',h/'admit-window.py','viewer',phone]);rc=proc.wait()
        assert not Path('/proc',str(proc.pid)).exists()
        info.update(started=True,pid=proc.pid,exit_code=rc)
        if rc or not actual.is_file():
            store(result,dict(**info,passed=False,attempts=[str(f) for f in h.glob('viewer-attempt-*')],finished=now()));return
    close=ck.completed_viewer(actual,304)
    rr=Path(close['report']);d=read(rr)
    assert all(obj['saveAsVerified'] for obj in d['downloads'].values())
    info.update(passed=True,physical=str(actual),physical_sha256=sha(actual),full_catalog_sha256=sha(full),report_sha256=sha(rr),views=len(d['views']),downloads=d['downloads'],finished=now())
    store(result,info)
if __name__=='__main__':
    with (w/'later-31304-viewer.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);main()
