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
    'closeups': ['map-fuzhou-road-three-round-doors-and-eastern-steps', 'map-three-upper-arches-and-stone-brackets'],
    'distant': ['map-distant'],
}
PREFIX = 'city-31283/independent-processes'

def read(path):
    return json.loads(path.read_bytes())

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def check_stage(folder, phase, source, prior_street=None):
    rc = read(folder / 'closed.json')
    basename = 'control-browser.json' if phase == 'before' else 'main-browser.json'
    record = read(folder / basename)
    assert rc['order'] == 283 and rc['phase'] == record['section'] == phase
    assert rc['exit'] == rc['exit_code'] == 0 and rc['node_closed'] and rc['chromium_pids']
    assert not rc['remaining'] and not rc['remaining_chromium']
    assert rc['report_sha256'] == digest(folder / basename)
    assert record['completed'] and record['scriptSha256'] == rc['driver_sha256'] == digest(source)
    if phase == 'distant':
        view, = [item for item in record['views'] if item['view'] == 'map-distant']
        asset = view['asset']
        verified = asset['verifiedAsset']
        marker = view['visibleLandmarkLabel']
        assert asset['id'] == verified['modelId'] == record['id']
        assert asset['visible'] and asset['status'] == 'loaded' and asset['variant'] == 'distant'
        assert verified['variant'] == 'lod' and asset['triangles'] == 10540
        assert verified['sha256'] == '1fd44526bffea0f795192148133978f5cb0543f57b13b3e596a23c8950d06663'
        assert verified['bytes'] == 1129700
        assert any(f['file'] == verified['file'] and f['loadedByScene']
                   and (f['sha256'], f['bytes']) == (verified['sha256'], verified['bytes'])
                   for f in record['files'])
        assert not view['contextLost'] and view['glError'] == 0
        assert record['id'] == marker['id'] or record['id'] in marker['memberIds']
        assert view['pick'] == marker['id']
    if phase=='distant' and record.get('capture_mode')=='headless-compositor':
        assert not record.get('displayCaptures')
        shot,=record['screenshots']
        composite,=record['compositorCaptures']
        gl,=record['webglCaptures']
        assert shot['file']==composite['file']=='map-distant.png'
        assert composite['source']=='Page.captureScreenshot' and composite['fromSurface'] is True
        assert not composite['captureBeyondViewport']
        assert composite['sha256']==shot['sha256']==digest(folder/shot['file'])
        assert shot['bytes']==(folder/shot['file']).stat().st_size
        assert gl['sha256']==digest(folder/gl['file']) and gl['bytes']==(folder/gl['file']).stat().st_size
        v=record['compositorViewport'];bounds=composite['bounds'];canvas=composite['drawingBuffer']
        assert bounds['dpr']==v['deviceScaleFactor']==1
        assert [v['width'],v['height']]==[bounds['width'],bounds['height']]
        assert canvas['width']==gl['width'] and canvas['height']==gl['height']
        with Image.open(folder/shot['file']) as page,Image.open(folder/gl['file']) as rendered:
            assert page.size==(v['width'],v['height']) and rendered.size==(gl['width'],gl['height'])
            for im in (page,rendered):
                assert max(hi-lo for lo,hi in im.convert('RGB').getextrema())>15
        return [shot['file']]
    calibration = record['viewportCalibration']
    assert digest(folder / calibration['image']) == calibration['sha256']
    shots = record['screenshots']
    assert [x['file'] for x in shots] == [stem + '.png' for stem in STAGES[phase]]
    assert len(record['displayCaptures']) == len(record['webglCaptures']) == len(shots)
    sessions=record.get('sessionsByFeature',[])
    if sessions:
        assert len(sessions)==len(shots)==2 and len({v['pid'] for v in sessions})==2
        issued_pids=set(rc['chromium_pids'])
        if record.get('entrancePhysical'):
            previous=read(folder/'earlier-closed.json')
            original=read(folder/'after-entrance.json')
            assert previous['exit']!=0 and previous['remaining']==[] and previous['node_closed']
            assert digest(folder/'earlier-actual-driver.cjs')==previous['driver_sha256']==original['scriptSha256']
            assert previous['report_sha256']==digest(folder/'earlier-main-browser.json')
            assert original['completed'] and original['sessionsByFeature']==sessions[:1]
            assert sessions[0]['pid'] in previous['chromium_pids'] and sessions[1]['pid'] in rc['chromium_pids']
            assert original['screenshots'][0]==shots[0]
            issued_pids.update(previous['chromium_pids'])
        if record.get('priorStreet'):
            trace=record['priorStreet']
            previous_dir = prior_street or folder/'earlier-street-attempt'
            previous=read(previous_dir/'closed.json')
            signed=read(previous_dir/'main-browser.json')
            assert previous['exit']==trace['phaseExit']==1 and previous['node']==trace['node']
            assert previous['node_closed'] and not previous['remaining']
            assert digest(previous_dir/'actual-driver.cjs')==trace['sourceSha256']==previous['driver_sha256']
            assert digest(previous_dir/'main-browser.json')==trace['reportSha256']==previous['report_sha256']
            assert trace['completedCapture']==shots[0]==signed['screenshots'][0]
            assert sessions[0]['pid']==trace['chromium'] and trace['chromium'] in previous['chromium_pids']
            assert sessions[0]['closed'] and sessions[0]==signed['sessionsByFeature'][0]
            issued_pids.update(previous['chromium_pids'])
        assert all(v['closed'] and v['pid'] in issued_pids for v in sessions)
    for idx,(shot,display,webgl) in enumerate(zip(shots, record['displayCaptures'], record['webglCaptures'])):
        if sessions:
            calibration=sessions[idx]['calibration']
            assert digest(folder/calibration['image'])==calibration['sha256']

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
    assert r['passed'] and not r['pageErrors'] and r['route'] == 'russell-company-fuzhou-three-bay-front.html'
    assert len(r['views']) == 6
    assert {(x['viewport']['width'],x['role']) for x in r['views']} == {(width,role) for width in (390,1250) for role in ('full','lod')}
    for row in r['views']:
        assert digest(folder / row['filename']) == row['sha256']
    assert set(r['downloads']) == {'full','lod','raw','native'}
    for row in r['downloads'].values():
        f = folder/'saved'/row['file']
        assert row['saveAsVerified'] and f.stat().st_size == row['bytes'] and digest(f)==row['sha256']
    return ['standalone/'+row['filename'] for row in r['views']]

def verify(audit,order,names):
    assert order == 283
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
        assert r['order']==348 and r['passed'] and r['exit']==0 and not r['remaining']
    approved.update([PREFIX+'/process-index.json',PREFIX+'/verify-283-processes.py'])
    assert approved <= set(names)
    return approved
