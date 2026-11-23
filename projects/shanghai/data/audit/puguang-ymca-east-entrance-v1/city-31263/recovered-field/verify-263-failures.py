"""Independently read the released Puguang YMCA map attempts and their complete captures."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageChops

def verify(audit, order, names):
    assert order == 263
    prefix='city-31263/recovered-field'
    root=Path(audit)/prefix
    index=root/'field-process-index.json'
    sha=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
    read=lambda file:json.loads(file.read_bytes())
    assert sha(index)=='3e7e2674e7c539c908191e1e8f79acbe7b3904ef3b455f6fdaedada78e543358'
    entries=read(index)
    keep={prefix+'/'+index.name}
    assert entries['order']==order and set(entries['successes'])==set(entries['expected_successes'])
    for failed,group in ((True,entries['attempts']), (False,entries['successes'])):
        for item in group.values():
            directory=item['directory']
            parent=root/directory
            assert not Path(directory).is_absolute() and '..' not in Path(directory).parts
            listed=item['files']
            assert {'closed.json','executed-driver.cjs','run.log'}<=set(listed)
            for name,meta in listed.items():
                assert not Path(name).is_absolute() and '..' not in Path(name).parts
                file=parent/name
                assert sha(file)==meta['sha256'] and file.stat().st_size==meta['bytes']
                keep.add(prefix+'/'+directory+'/'+name)
            c=read(parent/'closed.json')
            r=read(parent/item['report']) if item['report'] else None
            stage=item['phase']
            assert c['order']==order and c['phase']==stage
            assert c['node']>0 and c['node_closed'] and c['remaining']==c['remaining_chromium']==[]
            assert c['exit']==c['exit_code']==item['exit_code']
            assert c['driver_sha256']==sha(parent/'executed-driver.cjs')
            if r is None:
                assert failed and c['report_sha256'] is None
                if c['exit_code']==0:
                    assert stage=='before' and directory=='attempts/restart-01-report-removed'
                    assert {'map-before.png','map-before-webgl.png','map-before-x11-root.png'}<=set(listed)
                    assert 'control-browser.json' not in listed and c['chromium_pids']
                else:
                    assert c['exit_code']!=0
                assert Path(c['report']).name not in listed
                if c['exit_code']!=0:assert not c['chromium_pids']
                continue
            assert c['phase']==r['section'] and c['report_sha256']==sha(parent/item['report'])
            assert c['driver_sha256']==sha(parent/'executed-driver.cjs')==r['scriptSha256']
            assert r['caseSha256']==entries['case_sha256'] and r['id']=='huangpu-puguang-ymca-east-entrance'
            assert r['server']=='http://127.0.0.1:'+('31262/' if stage=='before' else '31263/')
            assert r['mode']==('frozen-before' if stage=='before' else 'delivered')
            if failed:
                assert not r['completed'] and (r.get('failure') or c['exit_code']!=0 or not r['screenshots'])
                assert r.get('failure')==item.get('failure')
            else:
                assert c['exit_code']==0 and r['completed'] and r['screenshots']
            if 'exit.json' in listed:
                e=read(parent/'exit.json')
                assert e['code']==c['exit_code'] and e['phase']==stage and e['driver_sha256']==c['driver_sha256']
                assert e['case_sha256']==entries['case_sha256']
            for pic in [*r['screenshots'],*r.get('webglCaptures',[])]:
                assert listed[pic['file']]['sha256']==pic['sha256'] and listed[pic['file']]['bytes']==pic['bytes']
            cal=r.get('viewportCalibration')
            if cal:
                assert listed[cal['image']]['sha256']==cal['sha256']
            for i,cap in enumerate(r.get('displayCaptures',[])):
                screen=parent/cap['displayImage']
                assert listed[screen.name]['sha256']==cap['displayImageSha256']
                m=re.fullmatch(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)',cap['rectangle'])
                assert m and cal
                w,h,x,y=map(int,m.groups())
                assert (x,y,w,h)==tuple(cal[k] for k in ('x','y','width','height'))
                base=screen.name.removesuffix('-x11-root.png')+'.png'
                assert base in listed
                with Image.open(parent/base) as crop,Image.open(screen) as display:
                    assert crop.size==(w,h)
                    assert not ImageChops.difference(crop.convert('RGB'),display.crop((x,y,x+w,y+h)).convert('RGB')).getbbox()
    old_meta=entries['pre_reset_metadata']
    for name,meta in old_meta.items():
        file=root/'pre-reset'/name
        assert file.stat().st_size==meta['bytes'] and sha(file)==meta['sha256']
        keep.add(prefix+'/pre-reset/'+name)
    old=read(root/'pre-reset/recovery-of-old-files.json')
    assert old['pre_reset_index_sha256']==sha(root/'pre-reset/pre-reset-field-process-index.json')
    rows=old['old_paths_with_evidence']
    assert old['old_paths']==len(rows)==85 and old['unique_old_digests']==len({r['sha256'] for r in rows.values()})==50
    assert set(old['identically_available_digests'])=={v['sha256'] for v in rows.values() if 'retained_as' in v}
    for record in rows.values():
        if 'retained_as' in record:
            assert sha(root/'pre-reset'/record['retained_as'])==record['sha256']
    assert keep<=set(names)
    return keep
