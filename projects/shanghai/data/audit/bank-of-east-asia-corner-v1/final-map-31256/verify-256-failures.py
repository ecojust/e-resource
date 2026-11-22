"""Verify the original 256 process exits, screenshots and subordinate desktop, phone and architecture records."""
from pathlib import Path
import json,hashlib,re
from PIL import Image,ImageChops
def verify(audit,order,names):
    assert order==256
    audit=Path(audit);root=audit/'final-map-31256'
    read=lambda f:json.loads(f.read_bytes())
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    index=root/'verified-attempt-index.json';assert sha(index)=='0192120f31d32a3df856ca65729294fa88db6df60f07c1b668871e7675bdac1c'
    ix=read(index);assert ix['order']==256 and {'before-01-original','before-02-neighbor-field'}<=ix['attempts'].keys()
    keep=set()
    for sig,path in ix['used_drivers'].items():assert sha(root/path)==sig
    def reported(p,phase):
        d=read(p);assert d['phase']==phase and d['id']=='huangpu-bank-of-east-asia-corner'
        assert d['server']=='http://127.0.0.1:'+('31255' if phase=='before' else '31256')+'/'
        assert d['scriptSha256'] in ix['used_drivers'] and len(d['caseSha256'])==64
        for item in d['screenshots']:
            img=p.parent/item['file'];assert img.parent==p.parent and img.stat().st_size==item['bytes'] and sha(img)==item['sha256']
        for capture in d.get('displayCaptures',[]):
            screen=p.parent/capture['displayImage'];assert sha(screen)==capture['displayImageSha256']
            img=p.parent/screen.name.replace('-x11-root.png','.png')
            match=re.fullmatch(r'(\d+)x(\d+)\+(\d+)\+(\d+)',capture['rectangle']);assert match
            width,height,x,y=map(int,match.groups())
            with Image.open(screen)as display,Image.open(img)as image:
                assert image.size==(width,height)
                assert ImageChops.difference(display.crop((x,y,x+width,y+height)).convert('RGB'),image.convert('RGB')).getbbox() is None
        for capture in d.get('webglCaptures',[]):
            path=capture.get('file');signature=capture.get('sha256')
            if path and signature:assert sha(p.parent/path)==signature
        return d
    for group in ('attempts','successes'):
        for name,setrow in ix[group].items():
            failed=group=='attempts';folder=root/setrow['directory'];files=setrow['files']
            if failed:
                actual={p.relative_to(folder).as_posix()for p in folder.rglob('*')if p.is_file()}
                if '.gitattributes' in actual:
                    assert set((folder/'.gitattributes').read_text().splitlines())<={n+' -whitespace'for n in files if n.endswith('.log')};actual.remove('.gitattributes')
                assert actual==files.keys()
            for k,v in files.items():
                assert sha(folder/k)==v
                if failed:keep.add((folder/k).relative_to(audit).as_posix())
            rec=read(folder/'process.json');phase=rec['phase']
            assert name==phase or name.startswith(phase+'-')
            assert rec['remaining_chromium']==rec['remaining_children']==[]
            reports={q:reported(q,phase) for q in folder.rglob('*-browser.json')}
            top=[p for p in reports if p.parent==folder]
            if not rec['chromium_pids']:
                assert name=='architecture-01-module-before-chromium' and not top and rec['exit_code']==1 and rec['report_sha256'] is None
                assert "Cannot find module './candidate-audit-groups.cjs'" in (folder/'architecture.log').read_text();continue
            assert rec['node_closed'] and rec['node_pids']
            if top:
                assert len(top)==1 and sha(top[0])==rec['report_sha256'];d=reports[top[0]]
                if failed:assert rec['exit_code']!=0 or not d['completed']
                else:assert rec['exit_code']==0 and d['completed'] and d['screenshots'] and not d['errors']
                if name=='before-01-original':assert 'Target crashed' in d['failure'] and not d['screenshots']
                if name=='before-02-neighbor-field':
                    assert "Cannot read properties of undefined (reading 'some')" in d['failure']
                    assert 'spec.existing_group_sources.some' in (root/ix['used_drivers'][d['scriptSha256']]).read_text().splitlines()[203]
            else:assert failed and rec['report_sha256'] is None and rec['exit_code']!=0
            for ledger,partkey,signature in [('directory-processes.json','part','reportSha256'),('architecture-stage-exits.json','kind','reportSHA256')]:
                track=folder/ledger
                if not track.is_file():continue
                items=read(track)
                for row in items:
                    assert row['pid']>0
                    if row.get('earlierAttempt'):
                        orig=root/ix['attempts'][row['earlierAttempt']]['directory']
                        oldproc=orig/'process.json';oldledger=orig/ledger
                        assert sha(oldproc)==row['originalProcessSHA256'] and sha(oldledger)==row['originalStageExitsSHA256']
                        assert row['pid'] in read(oldproc)['node_pids'] and row['originalDriverSHA256'] in ix['used_drivers']
                        assert any(o[partkey]==row[partkey] and o['pid']==row['pid'] and o['exit']==0 and o[signature]==row[signature] for o in read(oldledger))
                    else:assert row['pid']in rec['node_pids']
                    section=folder/row[partkey]
                    if row.get(signature):
                        report=section/'main-browser.json'
                        assert sha(report)==row[signature]
                        if row['exit']==0:assert read(report)['completed']
                    if row.get('driverSha256'):assert row['driverSha256'] in ix['used_drivers']
                if not failed:assert all(v['exit']==0 for v in items)
    assert keep<=set(names)
    return keep
