"""Read the two earlier failures, the eight actual city phases and the standalone files."""
from pathlib import Path
import hashlib,json

def verify(audit,order,names):
    assert order==266
    base=Path(audit)
    prefix='city-31266/independent-processes'
    folder=base/prefix
    def read(p):return json.loads(p.read_bytes())
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    index_file=folder/'process-index.json'
    index=read(index_file)
    assert index['order']==266
    verified={index_file.relative_to(base).as_posix()}
    for name,entry in index['files'].items():
        file=base/name
        assert name.startswith(prefix+'/') and file.stat().st_size==entry['bytes'] and sha(file)==entry['sha256'],name
        verified.add(name)
    assert verified<=set(names)
    for name,pattern in [('before-1-scope',"Cannot access 'source' before initialization"),('details-1-webgl','1281 !== 0')]:
        f=folder/'attempts'/name
        c=read(f/'closed.json')
        j=f/('control-browser.json' if name.startswith('before') else 'main-browser.json')
        assert c['exit_code']==1 and c['node_closed'] and not c['remaining'] and not c['remaining_chromium']
        assert sha(j)==c['report_sha256'] and sha(f/'actual-driver.cjs')==c['driver_sha256'] and pattern in (f/'run.log').read_text()
        assert not read(j)['completed'] and not read(j)['screenshots']
    note=read(folder/'attempts/331-waited-for-31331.json')
    assert note['host']==266 and note['order']==331 and note['deferred'] and not note['started'] and not note['viewer_started']
    assert note['host_closed_sha256']==sha(folder/'phone/closed.json')
    observed=read(folder/'visual-review.json')
    seen=set()
    for phase in ['before','phone','desktop','details','touch','architecture','closeups','distant']:
        f=folder/phase;c=read(f/'closed.json')
        report_file=f/('control-browser.json' if phase=='before' else 'main-browser.json');r=read(report_file)
        assert c['exit_code']==0 and c['node_closed'] and not c['remaining'] and not c['remaining_chromium'] and c['chromium_pids']
        assert sha(report_file)==c['report_sha256'] and sha(f/'actual-driver.cjs')==r['scriptSha256']==c['driver_sha256']==r['source_code_sha256']
        assert r['completed'] and not r['errors'] and not r['failed'] and all(v['glError']==0 for v in r['views'])
        for kind in ('screenshots','webglCaptures','displayCaptures'):
            for item in r[kind]:
                if kind=='displayCaptures':
                    assert sha(f/item['displayImage'])==item['displayImageSha256'];continue
                key=item['file'];assert sha(f/key)==item['sha256'] and (f/key).stat().st_size==item['bytes']
                if kind=='screenshots':
                    assert observed['images'][key]['sha256']==item['sha256'];seen.add(key)
        if phase in ('details','touch'):assert r['realBeacon']['pointer']['trusted'] and r['realBeacon']['landed']
        if phase=='architecture':assert len(r['ground'])==50
    f=folder/'standalone';r=read(f/'viewer.json');c=read(f/'closed.json')
    assert c['code']==0 and c['node_closed'] and not c['remaining_chromium'] and sha(f/'viewer.json')==c['report_sha256']
    assert len(r['views'])==4 and len(r['downloads'])==4 and r['passed'] and not r['pageErrors']
    for row in r['views']:
        name='standalone/'+row['filename'];assert observed['images'][name]['sha256']==sha(f/row['filename'])==row['sha256'];seen.add(name)
    for role,row in r['downloads'].items():
        saved=f/'saved'/row['file'];assert row['saveAsVerified'] and sha(saved)==row['sha256'] and saved.stat().st_size==row['bytes']
    assert len(seen)==14 and set(observed['images'])==seen
    return verified
