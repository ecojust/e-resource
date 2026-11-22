"""Validate original 255 browser outcomes against their published evidence."""
from pathlib import Path
import json,hashlib,re
from PIL import Image,ImageChops
def verify(audit,order,names):
    assert order==255
    audit=Path(audit);base=audit/'final-map-31255'
    read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source=base/'verified-attempt-index.json';assert sha(source)=='c5ff04d41c7a215c5f5a71184dc26656f903f47bd8ce02f61ce6c25b14b860b4'
    index=read(source);assert index['order']==255
    assert {'before-01-pre-chromium','before-02-target-crashed'}<=set(index['attempts'])
    accepted=set()
    for sign,rel in index['used_drivers'].items():assert sha(base/rel)==sign
    for row in index.get('archive_errors',{}).values():
        p=base/row['log'];assert sha(p)==row['sha256'] and "No space left on device: '/tmp/shanghai-main-255/evidence/phone'" in p.read_text()
        accepted.add(p.relative_to(audit).as_posix())
    for group in ('attempts','successes'):
        for name,case in index[group].items():
            folder=base/case['directory'];files=case['files']
            failed=group=='attempts'
            if failed:
                found={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
                if '.gitattributes'in found:
                    assert set((folder/'.gitattributes').read_text().splitlines())<={n+' -whitespace'for n in files if n.endswith('.log')}
                    found.remove('.gitattributes')
                assert found==set(files)
            for n,v in files.items():
                p=folder/n;assert sha(p)==v
                if failed:accepted.add(p.relative_to(audit).as_posix())
            c=read(folder/'process.json')
            assert c['remaining_children']==c['remaining_chromium']==[]
            phase=c['phase'];assert name==phase or name.startswith(phase+'-')
            if name=='before-01-pre-chromium':
                assert c['exit_code']==120 and c['node_pids']==c['chromium_pids']==[] and c['node_closed'] is False and c['report_sha256'] is None
                partial=read(folder/'partial-materialization.json')
                assert partial['exit']==120 and partial['bytes']==110592 and partial['sha256']=='40579ad30ee1969f7c3a3df8cd215700eeec82c4a5f83d3ddfa997055c4a8b51' and partial['log_bytes']==0
                assert set(files)=={'process.json','partial-materialization.json'}
                continue
            stage_log=phase+'-stage-exits.json'
            if stage_log in files:
                stages=read(folder/stage_log)
                assert stages and len({s['kind']for s in stages})==len(stages)
                for stage in stages:
                    child=folder/stage['kind']
                    if stage.get('earlierAttempt'):
                        prior=base/index['attempts'][stage['earlierAttempt']]['directory']
                        assert sha(prior/'process.json')==sha(child/'original-process.json')==stage['originalProcessSHA256']
                        assert stage['pid'] in read(prior/'process.json')['node_pids']
                        if phase=='desktop':assert sha(child/'original-stage-exits.json')==sha(prior/stage_log)
                        else:
                            original=next(s for s in read(prior/stage_log) if s['kind']==stage['kind'])
                            assert original['pid']==stage['pid'] and original['exit']==stage['exit']==0
                        assert stage['originalDriverSHA256']==sha(child/'original-driver.cjs') and stage['originalDriverSHA256'] in index['used_drivers']
                        assert sha(child/'main-browser.json')==stage['reportSHA256']==sha(prior/stage['kind']/'main-browser.json')
                        for origin in (prior/stage['kind']).glob('*.png'):assert sha(origin)==sha(child/origin.name)
                    else:assert stage['pid'] in c['node_pids']
                    child_report=child/'main-browser.json'
                    if child_report.is_file():
                        rep=read(child_report)
                        assert rep['scriptSha256'] in index['used_drivers']
                        if 'phase' in rep:assert rep['phase']==phase
                        else:assert name=='architecture-09-display-bounds' and stage['kind']=='balcony' and not rep['completed'] and 'opposite corners' in rep['failure']
                        assert rep['server']=='http://127.0.0.1:31255/' and rep['id']=='huangpu-hardoon-building-chamfer'
                        for shot in rep['screenshots']:
                            image=child/shot['file'];assert image.stat().st_size==shot['bytes'] and sha(image)==shot['sha256']
                        for gl in rep.get('webglCaptures',[]):
                            image=child/gl['file'];assert image.stat().st_size==gl['bytes'] and sha(image)==gl['sha256']
                        if 'viewportCalibration' in rep:
                            frame=rep['viewportCalibration'];assert sha(child/frame['image'])==frame['sha256']
                if name=='desktop-08-split-initial':
                    assert len(stages)==1 and stages[0]['kind']=='initial' and stages[0]['exit']==c['exit_code']==1
                    assert c['report_sha256'] is None and not rep['completed'] and not rep['screenshots']
                    assert 'Target crashed' in rep['failure'] and 'page.evaluate' in rep['failure'] and c['node_closed'] and len(c['chromium_pids'])==8
            reports=[n for n in files if '/' not in n and n.endswith('-browser.json')]
            if not reports:
                assert failed and c['report_sha256'] is None
                continue
            assert len(reports)==1 and c['report_sha256']==files[reports[0]] and c['node_closed'] and c['node_pids'] and c['chromium_pids']
            rep=read(folder/reports[0])
            assert rep['phase']==phase and rep['id']=='huangpu-hardoon-building-chamfer'
            assert rep['server']=='http://127.0.0.1:'+('31254' if phase=='before' else '31255')+'/'
            assert rep['scriptSha256'] in index['used_drivers'] and len(rep['caseSha256'])==64
            for shot in rep['screenshots']:
                path=folder/shot['file'];assert sha(path)==shot['sha256'] and path.stat().st_size==shot['bytes']
            captures=rep.get('displayCaptures',[])
            if captures:
                assert len(captures)==len(rep['screenshots'])
                for capture,shot in zip(captures,rep['screenshots']):
                    proof=folder/capture['displayImage'];assert sha(proof)==capture['displayImageSha256']
                    width,height,x,y=map(int,re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)',capture['rectangle']).groups())
                    with Image.open(proof)as screen,Image.open(folder/shot['file'])as frame:
                        assert frame.size==(width,height)
                        assert ImageChops.difference(screen.crop((x,y,x+width,y+height)).convert('RGB'),frame.convert('RGB')).getbbox() is None
            if failed and name.startswith('desktop-'):
                assert c['node_closed'] and not rep['completed']
                if name.split('-')[1] in ['01','02','03','04','05','06','07']:
                    assert [p['file']for p in rep['screenshots']]==['map-desktop.png']
                    if name=='desktop-05-single-process':
                        assert c['exit_code']==247 and len(c['chromium_pids'])==1 and 'finished'not in rep
                    else:assert c['exit_code']==1 and 'Target crashed' in rep['failure']
            if name=='before-03-near-transfer':
                assert c['exit_code']==1 and 'Timeout 240000ms exceeded' in rep['failure'] and not rep['screenshots'] and rep['failureState']
            if name=='before-04-after-near-loaded':
                assert c['exit_code']==1 and 'Target crashed' in rep['failure'] and not rep['screenshots']
            if failed:
                assert c['exit_code']!=0 or not rep['completed']
                if name=='before-02-target-crashed':
                    assert c['exit_code']==1 and not rep['completed'] and not rep['screenshots'] and 'Target crashed' in rep['failure']
                    assert rep['scriptSha256']=='40b7c3472bf0fd42dbaabc69b88157369ee98577fc5c94aaf5be663a5465584d'
            else:
                assert c['exit_code']==0 and rep['completed'] and rep['screenshots'] and not rep['errors']
    assert accepted<=set(names)
    return accepted
