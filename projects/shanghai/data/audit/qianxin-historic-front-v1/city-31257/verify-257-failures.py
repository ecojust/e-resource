"""Read every retained city session of case 257, including its unfinished pictures and exits."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageChops

def verify(audit,order,names):
    assert order==257
    prefix='city-31257'
    root=Path(audit)/prefix
    sha=lambda file:hashlib.sha256(file.read_bytes()).hexdigest()
    read=lambda file:json.loads(file.read_bytes())
    index=root/'field-process-index.json'
    assert sha(index)=='bcfd797101b83d02948ac3e9be5e0c66fb250cce3420595747dde7517c269010'
    entries=read(index);keep={prefix+'/'+index.name}
    assert entries['order']==257 and len(entries['attempts'])>=2
    assert set(entries['successes'])==set(entries['expected_successes'])
    for failed,group in ((True,entries['attempts']),(False,entries['successes'])):
        for key,item in group.items():
            phase=item['phase'];assert phase in ('before','phone','desktop')
            rel=item['directory'];parent=root/rel;assert '..' not in Path(rel).parts and not Path(rel).is_absolute()
            assert {p for p in ('closed.json',item['report'],'process.log','actual-driver.cjs')}<=item['files'].keys()
            for filename,record in item['files'].items():
                assert not Path(filename).is_absolute() and '..' not in Path(filename).parts
                p=parent/filename;assert sha(p)==record['sha256'] and p.stat().st_size==record['bytes']
                keep.add(prefix+'/'+rel+'/'+filename)
            c=read(parent/'closed.json');r=read(parent/item['report'])
            assert c['order']==257 and c['node_closed'] and c['exit']==c['exit_code']==item['exit_code']
            assert c['phase']==phase and c['remaining']==c['remaining_chromium']==[]
            assert c['node_pid']>0 and c['finished']>=c['start']
            assert set(map(int,c.get('chromium_birth_times',{})))==set(c['chromium_pids'])
            assert c['report_sha256']==sha(parent/item['report'])
            assert c['process_log_sha256']==sha(parent/'process.log')
            assert r['id']=='huangpu-qianxin-building-historic-front' and r['base']=='http://127.0.0.1:'+('31256' if phase=='before' else '31257')+'/'
            assert r['script_sha256']==sha(parent/'actual-driver.cjs') and r['signed_input_sha256']==entries['signed_input_sha256']
            assert r['mode']==('before' if phase=='before' else 'after') and r['passed'] is (not failed)
            if failed:
                assert r.get('failure')==item['failure'] and item['failure']
            else:
                assert c['exit_code']==0 and r['completed'] and r['browser_closed'] and r['captures']
            for capture in r['captures']:
                name=capture['file'];p=parent/name
                assert name in item['files'] and sha(p)==capture['sha256'] and p.stat().st_size==capture['bytes']
            calibration=r.get('viewportCalibration')
            if calibration:
                assert sha(parent/calibration['file'])==calibration['sha256']
            for capture in r.get('displayCaptures',[]):
                assert calibration
                p=parent/capture['root'];q=parent/capture['file']
                assert sha(p)==capture['root_sha256'] and sha(q)==capture['sha256']
                x,y,w,h=capture['rect'];assert [x,y,w,h]==[calibration[k]for k in ('x','y','width','height')]
                with Image.open(p) as screen,Image.open(q) as image:
                    assert image.size==(w,h)
                    assert ImageChops.difference(screen.crop((x,y,x+w,y+h)).convert('RGB'),image.convert('RGB')).getbbox() is None
            for f in r.get('saved_downloads',[]):
                p=parent/f['saved'];assert f['saveAsVerified'] and p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
    assert keep<=set(names)
    return keep
