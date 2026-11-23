"""Read the one city and two guest failures, the eight actual city phases and the standalone files."""
from pathlib import Path
import hashlib,json

def verify(audit,order,names):
    assert order==267
    base=Path(audit)
    prefix='city-31267/independent-processes'
    folder=base/prefix
    def read(p):return json.loads(p.read_bytes())
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    index_file=folder/'process-index.json'
    index=read(index_file)
    assert index['order']==267
    verified={index_file.relative_to(base).as_posix()}
    for name,entry in index['files'].items():
        file=base/name
        assert name.startswith(prefix+'/') and file.stat().st_size==entry['bytes'] and sha(file)==entry['sha256'],name
        verified.add(name)
    assert verified<=set(names)
    f=folder/'attempts/before-01-neighbor-ownership'
    c=read(f/'closed.json');data=read(f/'control-browser.json');log=(f/'run.log').read_text()
    assert c['exit_code']==1 and c['node_closed'] and not c['remaining'] and not c['remaining_chromium'] and not data['completed'] and not data['screenshots']
    assert c['driver_sha256']==sha(f/'actual-driver.cjs') and c['report_sha256']==sha(f/'control-browser.json')
    assert all(value in log for value in ['1588','1766','deepStrictEqual','actual: []'])
    current=read(folder/'before/control-browser.json')['views'][0]['group']
    assert {1588,1766} <= set(current['feature_local_ids']) and len(current['feature_local_ids'])==16 and current['clip_feature_local_ids']==[]
    f=folder/'attempts/332-native-20261123T031825';n=read(f/'332-native-deferred.json')
    assert n['started'] and n['child_exit']==1 and n['host_closed_sha256']==sha(folder/'before/closed.json')
    for k in ('launch_process','launch_log'):assert n[k+'_sha256']==sha(f/Path(n[k]).name)
    assert '/proc/742711/comm' in (f/Path(n['launch_log']).name).read_text()
    f=folder/'attempts/332-viewer-01-contract-key';n=read(f/'332-viewer-deferred.json');q=read(f/'267-viewer-deferred.json')
    assert n['deferred'] and not n['viewer_started'] and len(n['missing'])==3 and n['host_closed_sha256']==sha(folder/'phone/closed.json')
    assert q['started'] and q['child_exit']==1 and q['host_receipt_sha256']==sha(folder/'phone/closed.json')
    for k in ('launch_process','launch_log'):assert q[k+'_sha256']==sha(f/Path(q[k]).name)
    assert "KeyError: 'viewer_module_sha256'" in (f/Path(q['launch_log']).name).read_text()
    for kind,phase in [('native','before'),('viewer','phone')]:
        returned=read(folder/f'332-{kind}-returned.json');assert returned['passed'] and returned['host_closed_sha256']==sha(folder/phase/'closed.json')
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
        if phase=='architecture':assert len(r['ground'])==75
    f=folder/'standalone';r=read(f/'viewer.json');c=read(f/'closed.json')
    assert c['code']==0 and c['node_closed'] and not c['remaining_chromium'] and sha(f/'viewer.json')==c['report_sha256']
    assert len(r['views'])==4 and len(r['downloads'])==4 and r['passed'] and not r['pageErrors']
    for row in r['views']:
        name='standalone/'+row['filename'];assert observed['images'][name]['sha256']==sha(f/row['filename'])==row['sha256'];seen.add(name)
    for role,row in r['downloads'].items():
        saved=f/row['saved'];assert row['saveAsVerified'] and sha(saved)==row['sha256'] and saved.stat().st_size==row['bytes']
    assert len(seen)==14 and set(observed['images'])==seen
    return verified
