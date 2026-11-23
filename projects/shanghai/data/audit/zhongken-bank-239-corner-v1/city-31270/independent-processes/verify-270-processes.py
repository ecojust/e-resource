"""Verify the eight map processes, original display captures and the four ordinary views."""
from pathlib import Path
import hashlib
import json

PREFIX='city-31270/independent-processes'
STAGES=('before','phone','desktop','details','touch','architecture','closeups','distant')
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    return json.loads(p.read_bytes())
def verify(audit,order,names):
    assert order==270
    root=Path(audit)
    dirpath=root/PREFIX
    index=read(dirpath/'process-index.json')
    assert index['order']==270
    seen={PREFIX+'/process-index.json',PREFIX+'/verify-270-processes.py'}
    for name,row in index['files'].items():
        assert name.startswith(PREFIX+'/') and '..' not in Path(name).parts
        f=root/name
        assert f.stat().st_size==row['bytes'] and sha(f)==row['sha256'],name
        seen.add(name)
    obs=read(dirpath/'visual-review.json')['images']
    visuals=set()
    for phase in STAGES:
        p=dirpath/phase
        c=read(p/'closed.json')
        assert c['order']==270 and c['phase']==phase and c['exit']==c['exit_code']==0 and c['node_closed'] and c['cdp_closed'] and c['chromium_pids'] and not c['remaining'] and not c['remaining_chromium']
        report=p/('control-browser.json' if phase=='before' else 'main-browser.json')
        r=read(report)
        assert r['completed'] and r['section']==phase and not r['errors'] and r['server']==f"http://127.0.0.1:{31269 if phase=='before' else 31270}/"
        assert sha(report)==c['report_sha256'] and sha(p/'actual-driver.cjs')==c['driver_sha256']==r['source_code_sha256']==r['scriptSha256']
        calibration=r['viewportCalibration']
        assert sha(p/calibration['image'])==calibration['sha256']
        screens=r['screenshots']
        assert len(screens)==len(r['webglCaptures'])==len(r['displayCaptures'])
        for s,g,d in zip(screens,r['webglCaptures'],r['displayCaptures']):
            assert sha(p/s['file'])==s['sha256'] and sha(p/g['file'])==g['sha256'] and sha(p/d['displayImage'])==d['displayImageSha256']
            assert obs[s['file']]['sha256']==s['sha256'] and obs[s['file']]['observation']
            visuals.add(s['file'])
    p=dirpath/'standalone';r=read(p/'viewer.json');c=read(p/'closed.json')
    assert c['code']==0 and c['node_closed'] and c['chromium_pids'] and not c['remaining_chromium'] and c['report_sha256']==sha(p/'viewer.json')
    assert r['passed'] and len(r['views'])==4 and not r['pageErrors'] and set(r['downloads'])=={'full','lod','raw','native'}
    for v in r['views']:
        n=v.get('filename',v.get('file'));key='standalone/'+n
        assert sha(p/n)==obs[key]['sha256']==v['sha256'] and obs[key]['observation']
        visuals.add(key)
    for role,v in r['downloads'].items():
        candidates=[f for f in (p/'saved').rglob('*') if f.is_file() and sha(f)==v['sha256']]
        assert len(candidates)==1 and candidates[0].stat().st_size==v['bytes']
    assert visuals==set(obs)
    assert seen<=set(names)
    return seen
