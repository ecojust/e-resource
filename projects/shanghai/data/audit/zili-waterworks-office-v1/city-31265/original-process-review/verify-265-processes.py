"""Verify the ten city sessions, the independent viewer and the two original interruptions."""
from pathlib import Path
from hashlib import sha256
import json
def verify(audit,order,names):
    assert order==265
    root=Path(audit);base='city-31265/';archive=base+'original-process-review/'
    def data(name):return json.loads((root/name).read_bytes())
    def sha(name):return sha256((root/name).read_bytes()).hexdigest()
    index=data(archive+'process-review-index.json');assert index['order']==265
    checked=set(index['files'])|{archive+'process-review-index.json',archive+'verify-265-processes.py'};assert checked<=set(names)
    for name,row in index['files'].items():
        assert name.startswith(base) and sha(name)==row['sha256'] and (root/name).stat().st_size==row['bytes']
    phases='control mobile-card mobile-pin desktop-card desktop-pin street roof brick-door side-arches distant'.split()
    assert phases==index['phases']
    review=data(base+'visual-review.json')['images'];assert len(review)==14
    for name in phases:
        stub=base+'actual-browser-phases/'+name;c=data(stub+'-closed.json');r=data(stub+'.json')
        assert c['node_closed'] and c['cdp_closed'] and c['exit_code']==0 and not c['remaining_chromium']
        assert c['report_sha256']==sha(stub+'.json') and c['source_code_sha256']==r['scriptSha256']==sha(stub+'/actual-driver.cjs')
        assert r['completed'] and not r['failed'] and not r['errors']
        q,=r['screenshots'];assert sha(base+q['file'])==q['sha256']==review[q['file']]['sha256']
    viewer=data(base+'standalone/viewer.json');assert viewer['passed'] and len(viewer['views'])==4
    assert data(base+'standalone/closed.json')['exit_code']==0
    for frame in viewer['views']:
        k='standalone/'+frame['filename'];assert sha(base+k)==frame['sha256']==review[k]['sha256']
    for kind,item in viewer['downloads'].items():assert sha(archive+'standalone-saved/'+item['file'])==item['sha256']
    assert set(viewer['downloads'])=={'raw','full','lod','native'}
    source=(root/(archive+'ten-city-and-archive-exit.log')).read_text()
    assert 'All 265 main-scene sessions have closed' in source and 'FileNotFoundError' in source and 'r684closedhttp' in source and 'exit status 1' in source
    full=archive+'recovered-31265-all-http.json';assert (root/full).stat().st_size==587608 and data(full)['passed']
    final=data(archive+'265-released.json');assert final['order']==265 and final['exit_code']==0 and len(final['screenshots'])==10
    hold=data(archive+'330-deferred.json');assert not hold['started'] and not hold['attempted'] and len(hold['missing'])==2
    actual=data(archive+'330-viewer-closed.json');assert actual['passed'] and actual['exit_code']==0 and not actual['remaining'] and len(actual['chromium_pids'])>=2 and actual['host_receipt_sha256']==hold['source_sha256']
    g=data(archive+'330-viewer.json');assert len(g['views'])==6 and len(g['downloads'])==4 and not g['pageErrors']
    assert all(data(archive+'330-'+v+'-node-exit.json')['exit']==0 for v in ['desktop','mobile'])
    return checked
