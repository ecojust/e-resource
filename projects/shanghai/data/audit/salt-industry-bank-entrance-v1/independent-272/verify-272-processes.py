"""Re-read the completed Salt Industry Bank city frames, the rejected calibration, and the independent viewer."""
from pathlib import Path
import hashlib,json
def verify(audit,order,names):
    assert order==272
    root=Path(audit);base=root/'independent-272'
    read=lambda p:json.loads(p.read_bytes())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    index=read(base/'process-review.json')
    checked={'independent-272/process-review.json','independent-272/verify-272-processes.py'}
    for name,record in index['files'].items():
        assert name.startswith('independent-272/') and '..' not in Path(name).parts
        p=root/name
        assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],name
        checked.add(name)
    assert checked<=set(names)
    observation=read(base/'visual-review.json')['images'];seen=set()
    for phase,count in [('before',1),('phone',2),('desktop',2),('architecture',4),('mouse',1),('touch',1),('distant',1)]:
        d=base/phase;proc=read(d/'process.json');report=d/('control-browser.json' if phase=='before' else 'main-browser.json');r=read(report)
        assert proc['exit_code']==0 and proc['node_closed'] and proc['chromium_pids'] and not proc['remaining_children'] and not proc['remaining_chromium']
        assert sha(d/'actual-driver.cjs')==proc['driver_sha256']==r['source_code_sha256']==r['scriptSha256'] and sha(report)==proc['report_sha256']
        assert r['completed'] and not r['errors'] and not r['failed'] and len(r['screenshots'])==count and all(v['glError']==0 for v in r['views'])
        assert len(r['webglCaptures'])==len(r['displayCaptures'])==count
        for pics in ['screenshots','webglCaptures','displayCaptures']:
            for item in r[pics]:
                name=item['file'] if pics!='displayCaptures' else item['displayImage'];checksum=item['sha256'] if pics!='displayCaptures' else item['displayImageSha256']
                assert sha(d/name)==checksum
                if pics=='screenshots':seen.add(name);assert observation[name]['sha256']==checksum
        if phase in ('mouse','touch'):
            assert r['physicalSelections'] and all(a['input']==phase and a['selected']==a['label']==r['id'] and a['x']>0 and a['y']>0 for a in r['physicalSelections'])
        if phase=='architecture':assert len(r['ground'])==138 and all(a['expected']==a['found'] for a in r['ground']) and len(r['architecturalPixels'])==2
    for name,record in index.get('historical_attempts',{}).items():
        assert name in index['files']
        if record.get('exit_field'):
            assert read(root/name)[record['exit_field']]==record['exit']
    for name in index.get('guest_results',[]):
        outcome=read(root/name)
        assert outcome['order']==337 and outcome['host']==272
        phase='before' if name.endswith('native-result.json') else 'phone'
        assert outcome['source_sha256']==sha(base/phase/'process.json')
    f=base/'standalone';r=read(f/'viewer.json');c=read(f/'closed.json')
    assert c['exit']==0 and not c['remaining_observed'] and not c['chromium_remaining'] and sha(f/'viewer.json')==c['report_sha256'] and r['passed'] and not r['pageErrors']
    assert len(r['views'])==6 and set(r['downloads'])=={'raw','full','lod','native'}
    for item in r['views']:
        name=item['filename'];seen.add('standalone/'+name);assert observation['standalone/'+name]['sha256']==sha(f/name)==item['sha256']
    for role,item in r['downloads'].items():
        assert item['saveAsVerified'] and (f/item['saved']).stat().st_size==item['bytes'] and sha(f/item['saved'])==item['sha256']
    assert len(seen)==18 and seen==set(observation)
    return checked
