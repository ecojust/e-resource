"""Read original stage receipts, verify the X11 pixels and rehash every delivered file."""
from pathlib import Path
import hashlib
import json
import re

from PIL import Image, ImageChops

STAGES = {
    'before': ['map-before'],
    'phone': ['map-mobile'],
    'desktop': ['map-desktop'],
    'details': ['map-beacon-return'],
    'touch': ['map-touch-beacon-return'],
    'architecture': ['map-street-facade', 'map-roof'],
    'closeups': ['map-rounded-shopfront-and-corner-door', 'map-curved-steel-windows-and-parapet'],
    'distant': ['map-distant'],
}
PREFIX = 'city-31275/independent-processes'

def read(path):
    return json.loads(path.read_bytes())

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def check_stage(folder, phase, source):
    rc = read(folder / 'closed.json')
    basename = 'control-browser.json' if phase == 'before' else 'main-browser.json'
    record = read(folder / basename)
    assert rc['order'] == 275 and rc['phase'] == record['section'] == phase
    assert rc['exit'] == rc['exit_code'] == 0 and rc['node_closed'] and rc['chromium_pids']
    assert not rc['remaining'] and not rc['remaining_chromium']
    assert rc['report_sha256'] == digest(folder / basename)
    assert record['completed'] and record['scriptSha256'] == rc['driver_sha256'] == digest(source)
    calibration = record['viewportCalibration']
    assert digest(folder / calibration['image']) == calibration['sha256']
    shots = record['screenshots']
    assert [x['file'] for x in shots] == [stem + '.png' for stem in STAGES[phase]]
    assert len(record['displayCaptures']) == len(record['webglCaptures']) == len(shots)
    for shot, display, webgl in zip(shots, record['displayCaptures'], record['webglCaptures']):
        page = folder / shot['file']
        gl = folder / webgl['file']
        root = folder / display['displayImage']
        assert digest(page) == shot['sha256'] and page.stat().st_size == shot['bytes']
        assert digest(gl) == webgl['sha256'] and gl.stat().st_size == webgl['bytes']
        assert digest(root) == display['displayImageSha256']
        parts = re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)', display['rectangle'])
        width,height,x,y = map(int, parts.groups())
        assert (x,y) == (calibration['x'],calibration['y'])
        with Image.open(page) as p, Image.open(root) as full, Image.open(gl) as rendered:
            assert p.size == (width,height)
            assert ImageChops.difference(p.convert('RGB'),full.crop((x,y,x+width,y+height)).convert('RGB')).getbbox() is None
            assert rendered.size == (webgl['width'],webgl['height'])
            assert max(maximum-minimum for minimum,maximum in rendered.convert('RGB').getextrema())>15
    return [x['file'] for x in shots]

def check_standalone(folder):
    closed = read(folder / 'closed.json')
    r = read(folder / 'viewer.json')
    assert closed['code'] == 0 and closed['node_closed'] and not closed['remaining_chromium']
    assert closed['chromium_pids'] and digest(folder/'viewer.json') == closed['report_sha256']
    assert r['passed'] and not r['pageErrors'] and r['route'] == 'american-oriental-bank-rounded-corner.html'
    assert len(r['views']) == 6
    assert {v['filename'] for v in r['views']} == {f'viewer-{device}-{role}{suffix}.png' for device, role, suffix in [('desktop','full',''),('desktop','full','-oblique'),('desktop','full','-above'),('desktop','lod',''),('mobile','full',''),('mobile','lod','')]}
    assert {(x['viewport']['width'],x['role']) for x in r['views']} == {(width,role) for width in (390,1250) for role in ('full','lod')}
    for row in r['views']:
        assert digest(folder / row['filename']) == row['sha256']
    assert set(r['downloads']) == {'full','lod','raw','native'}
    for row in r['downloads'].values():
        f = folder/'saved'/row['file']
        assert row['saveAsVerified'] and f.stat().st_size == row['bytes'] and digest(f)==row['sha256']
    return ['standalone/'+row['filename'] for row in r['views']]

def verify(audit,order,names):
    assert order == 275
    audit=Path(audit)
    base=audit/PREFIX
    idx=read(base/'process-index.json')
    approved=set(idx['files'])
    for name,ref in idx['files'].items():
        assert name.startswith(PREFIX+'/')
        f=audit/name
        assert f.stat().st_size==ref['bytes'] and digest(f)==ref['sha256']
    reviewed=read(base/'visual-review.json')['images']
    checked=[]
    for phase in STAGES:
        folder=base/phase
        checked.extend(check_stage(folder,phase,base/'drivers'/read(folder/'closed.json')['driver_sha256']))
    checked.extend(check_standalone(base/'standalone'))
    assert len(checked)==len(reviewed)==16 and set(checked)==set(reviewed)
    for name,row in reviewed.items():
        assert row['observation'] and row['sha256'] == digest(audit / row['path'])
    for role in ['native','viewer']:
        r=read(base/'guest'/(role+'-closed.json'))
        assert r['order']==340 and r.get('physical_map_order',r.get('host'))==275 and r['all_processes_closed'] and r['exit']==0 and not r['remaining']
    approved.update([PREFIX+'/process-index.json',PREFIX+'/verify-275-processes.py'])
    assert approved <= set(names)
    return approved
