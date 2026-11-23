"""Check the ten Shanghai Money Guild map captures, original and new standalone visits, and both Sinan Road windows."""
from pathlib import Path
import hashlib,json
PREFIX='city-31277/independent-processes'
STAGES=('control','mobile-card','mobile-pin','desktop-card','desktop-pin','street','roof','arched-entrance','balcony-brackets','distant')
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(audit,order,names):
    assert order==277
    root=Path(audit);folder=root/PREFIX
    index=read(folder/'process-index.json');assert index['order']==order
    checked={PREFIX+'/verify-277-processes.py',PREFIX+'/process-index.json'}
    for n,item in index['files'].items():
        assert n.startswith(PREFIX+'/') and '..' not in Path(n).parts
        f=root/n;assert sha(f)==item['sha256'] and f.stat().st_size==item['bytes'],n
        checked.add(n)
    assert checked<=set(names)
    notes=read(folder/'visual-review.json')['images'];seen=set()
    for stage in STAGES:
        d=folder/stage;c=read(d/'closed.json');report=d/('control-browser.json'if stage=='control'else'main-browser.json')
        r=read(report);assert c['node_closed'] and c['cdp_closed'] and c['exit_code']==0 and c['chromium_pids'] and not c['remaining'] and not c['remaining_chromium']
        assert sha(d/'actual-driver.cjs')==r['scriptSha256']==c['source_code_sha256'] and sha(report)==c['report_sha256']
        assert r['completed'] and r['phase']==stage and not r['errors'] and not r['failed']
        cal=r['viewportCalibration'];assert sha(d/cal['image'])==cal['sha256']
        assert len(r['screenshots'])==len(r['webglCaptures'])==len(r['displayCaptures'])==1
        for k in ('screenshots','webglCaptures'):
            im,=r[k];f=d/im['file'];assert sha(f)==im['sha256'] and f.stat().st_size==im['bytes']
            if k=='screenshots':
                seen.add(f.name);assert notes[f.name]['sha256']==im['sha256'] and notes[f.name]['observation']
        frame,=r['displayCaptures'];assert sha(d/frame['displayImage'])==frame['displayImageSha256']
        for v in r['views']:assert v['glError']==0 and not v['contextLost']
        if stage in ('mobile-pin','desktop-pin'):
            assert any(b['landed']==r['id'] and b['pointer']['on_canvas'] and b['pointer']['trusted']for b in r['realBeaconInputs'])
        if stage=='street':
            assert len(r['ground'])==227 and all(p['found']==p['expected']for p in r['ground'])
    for phase,kind in [('control','native'),('mobile-pin','viewer')]:
        r=read(folder/'guest'/(kind+'-closed.json'))
        assert r['order']==342 and r['passed'] and r['exit_code']==0 and r['all_processes_closed'] and not r['remaining']
        assert r['host_receipt_sha256']==sha(folder/phase/'closed.json')
        if kind=='viewer':assert r['views']==6 and r['downloads']==4 and len(set(r['node_pids']))==2
    current=folder/'standalone';r=read(current/'viewer.json');c=read(current/'closed.json')
    assert c['passed'] and c['exit_code']==0 and not c['remaining'] and c['chromium']
    assert c['report_sha256']==sha(current/'viewer.json') and c['driver_sha256']==r['scriptSHA256']==sha(current/'formal-viewer.cjs')
    assert c['prior_sha256']==sha(folder/'distant/closed.json') and len(r['views'])==4
    for q in r['views']:
        n='standalone/'+q['filename'];assert notes[n]['sha256']==sha(current/q['filename'])==q['sha256'] and notes[n]['observation'];seen.add(n)
    before=folder/'original-standalone';original=read(before/'viewer.json');old_review=read(before/'earlier-six-review.json');old_close=read(before/'closed.json')
    assert old_close['node_closed']and old_close['exit']==0 and old_close['chromium_pids']and not old_close['remaining']
    assert old_review['original_report_sha256']==old_close['report_sha256']==sha(before/'viewer.json') and len(original['views'])==len(old_review['images'])==6
    for q in original['views']:assert q['sha256']==sha(before/q['filename'])==old_review['images'][q['filename']]['sha256'] and old_review['images'][q['filename']]['observation']
    assert r['downloads'].keys()==original['downloads'].keys()=={'raw','full','lod','native'}
    for role,item in r['downloads'].items():
        f=current/'saved'/item['file'];assert item['saveAsVerified'] and f.stat().st_size==item['bytes'] and sha(f)==item['sha256']==original['downloads'][role]['sha256']
    assert set(notes)==seen and len(seen)==14
    return checked
