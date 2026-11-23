"""Re-read the completed Zhongxing Bank city frames, the rejected architecture and host transitions, and the independent viewer."""
from pathlib import Path
import hashlib,json
def verify(audit,order,names):
    assert order==284
    root=Path(audit);base=root/'final-map-31284/independent-processes'
    read=lambda p:json.loads(p.read_bytes())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    index=read(base/'process-review.json')
    checked={'final-map-31284/independent-processes/process-review.json','final-map-31284/independent-processes/verify-284-processes.py'}
    for name,record in index['files'].items():
        assert name.startswith('final-map-31284/independent-processes/') and '..' not in Path(name).parts
        p=root/name
        assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],name
        checked.add(name)
    assert checked<=set(names)
    earlier=read(base/'earlier-six-review.json')
    earlier_report=base/'earlier-standalone/viewer.json'
    assert sha(earlier_report)==earlier['viewer_sha256'] and len(earlier['images'])==6
    for expected in read(earlier_report)['views']:
        n=expected.get('filename',expected.get('file'))
        actual=earlier['images'][n]
        assert actual['observation'] and sha(base/'earlier-standalone'/n)==actual['sha256']==expected['sha256']
    observation=read(base/'visual-review.json')['images'];seen=set()
    for phase,count in [('before',1),('phone',2),('desktop',2),('architecture',4),('mouse',1),('touch',1),('distant',1)]:
        d=base/phase;proc=read(d/'process.json');report=d/('control-browser.json' if phase=='before' else 'main-browser.json');r=read(report)
        assert proc['exit_code']==0 and proc['node_closed'] and proc['chromium_pids'] and not proc['remaining_children'] and not proc['remaining_chromium']
        assert sha(d/'actual-driver.cjs')==proc['driver_sha256']==r['scriptSha256'] and r.get('source_code_sha256',r['scriptSha256'])==r['scriptSha256'] and sha(report)==proc['report_sha256']
        assert r['completed'] and not r['errors'] and not r['failed'] and len(r['screenshots'])==count and all(v['glError']==0 for v in r['views'])
        compositor=r.get('capture_mode')=='headless-compositor'
        assert len(r['webglCaptures'])==count
        if compositor:
            assert phase in ('before','mouse','touch','distant') and not r.get('displayCaptures')
            assert len(r['compositorCaptures'])==count
        else:
            assert len(r['displayCaptures'])==count
        for pics in (['screenshots','webglCaptures'] if compositor else ['screenshots','webglCaptures','displayCaptures']):
            for item in r[pics]:
                name=item['file'] if pics!='displayCaptures' else item['displayImage'];checksum=item['sha256'] if pics!='displayCaptures' else item['displayImageSha256']
                assert sha(d/name)==checksum
                if pics=='screenshots':key=phase+'/'+name;seen.add(key);assert observation[key]['sha256']==checksum
        if phase in ('mouse','touch'):
            assert r['physicalSelections'] and all(a['input']==phase and a['selected']==r['id'] and ((a['group'] and r['id'] in a['members']) or (not a['group'] and a['label']==r['id'])) and a['x']>0 and a['y']>0 for a in r['physicalSelections'])
        if phase in ('mouse','touch'):
            for selection in r['physicalSelections']:
                pointer=selection['pointer']
                if isinstance(pointer,dict):
                    assert pointer['trusted'] is True and pointer['type']==phase
                else:
                    assert pointer and all(event.get('isTrusted',event.get('trusted',False)) for event in pointer)
        if 'selectionCapture' in r:
            assert phase in ('mouse','touch')
            capture=r['selectionCapture'];folder=d/'selection-origin';prior=read(folder/'process.json');source=read(folder/'main-browser.json')
            assert capture['sameBrowser'] is False and prior['exit_code']==capture['priorExit']
            assert sha(folder/'actual-driver.cjs')==prior['driver_sha256']==capture['driver']==source['scriptSha256']
            assert sha(folder/'main-browser.json')==prior['report_sha256']==capture['report']
            assert prior['node_closed'] and not prior['remaining_chromium'] and not prior['remaining_children']
            assert set(capture['chromiumPids'])==set(prior['chromium_pids']) and set(capture['chromiumPids']).isdisjoint(proc['chromium_pids'])
            assert source['physicalSelections']==r['physicalSelections'] and '#landmark='+r['id']+'&mode=overview' in capture['selectedURL']
            assert capture['selectedURL'].split('index.html',1)[1] in (folder/'run.log').read_text()
        if phase in ('mouse','touch') and (d/'pointer-activation/session-closed.json').is_file():
            ac=d/'pointer-activation';ticket=read(ac/'session-closed.json');render=read(d/'render-session-closed.json')
            assert ticket['exit_code']==render['exit_code']==0 and not ticket['remaining'] and not render['remaining']
            assert sha(ac/'actual-driver.cjs')==ticket['driver_sha256'] and sha(d/'actual-driver.cjs')==render['driver_sha256']
            assert ticket['report_sha256']==sha(ac/'main-browser.json')==r['reopenedSelection']['inputReportSha256']
            assert render['report_sha256']==sha(report) and set(ticket['chromium_pids']).isdisjoint(render['chromium_pids'])
            assert read(ac/'main-browser.json')['physicalSelections']==r['physicalSelections']
            for action in r['physicalSelections']:
                assert len(action['pointer'])>=2 and all(t['isTrusted'] for t in action['pointer'])
        if phase=='architecture':assert len(r['ground'])==30 and all(a['expected']==a['found'] for a in r['ground']) and len(r['architecturalPixels'])==2
    architecture=base/'architecture'
    field=read(architecture/'main-browser.json')
    for closeup in field['architecturalPixels']:
        targets=closeup['attempts'][-1]['targets']
        assert len(targets)==6 and all(t['clear'] and t['hit']=='CANVAS' and not t['beacon'] for t in targets)
    for phase in ('before','phone','desktop','architecture','mouse','touch','distant'):
        folder=base/phase;field=read(folder/('control-browser.json' if phase=='before' else 'main-browser.json'))
        from PIL import Image, ImageChops
        import re
        if field.get('capture_mode')=='headless-compositor':
            for shot,capture,gl in zip(field['screenshots'],field['compositorCaptures'],field['webglCaptures']):
                assert capture['method']=='Page.captureScreenshot' and capture['fromSurface'] is True
                assert (capture['file'],capture['sha256'])==(shot['file'],shot['sha256'])
                assert gl['width']==capture['canvas']['width'] and gl['height']==capture['canvas']['height']
                with Image.open(folder/shot['file']) as viewport,Image.open(folder/gl['file']) as buffer:
                    assert viewport.size==(capture['width'],capture['height'])
                    assert buffer.size==(gl['width'],gl['height'])
                    for im in (viewport,buffer):
                        assert max(hi-lo for lo,hi in im.convert('RGB').getextrema())>15
            continue
        for shot,display,gl in zip(field['screenshots'],field['displayCaptures'],field['webglCaptures']):
            m=re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)',display['rectangle']);assert m,display
            width,height,x,y=map(int,m.groups())
            with Image.open(folder/display['displayImage'])as rootim,Image.open(folder/shot['file'])as viewport,Image.open(folder/gl['file'])as buf:
                assert viewport.size==(width,height) and buf.size==(gl['width'],gl['height'])
                assert ImageChops.difference(viewport.convert('RGB'),rootim.crop((x,y,x+width,y+height)).convert('RGB')).getbbox() is None
    for name,record in index.get('historical_attempts',{}).items():
        assert name in index['files']
        if record.get('exit_field'):
            assert read(root/name)[record['exit_field']]==record['exit']
    for name in index.get('guest_results',[]):
        outcome=read(root/name)
        assert outcome['order']==349 and outcome['host']==284
        phase='before' if name.endswith('native-result.json') else 'phone'
        assert outcome['source_sha256']==sha(base/phase/'process.json')
    f=base/'standalone';r=read(f/'viewer.json');c=read(f/'closed.json')
    assert c['exit']==0 and not c['remaining_observed'] and not c['chromium_remaining'] and sha(f/'viewer.json')==c['report_sha256'] and r['passed'] and not r['pageErrors']
    assert len(r['views'])==6 and set(r['downloads'])=={'raw','full','lod','native'}
    for item in r['views']:
        name=item.get('filename',item.get('file'));seen.add('standalone/'+name);assert observation['standalone/'+name]['sha256']==sha(f/name)==item['sha256']
    for role,item in r['downloads'].items():
        assert item['saveAsVerified'] and (f/'saved'/item['file']).stat().st_size==item['bytes'] and sha(f/'saved'/item['file'])==item['sha256']
    assert len(seen)==18 and seen==set(observation)
    return checked
