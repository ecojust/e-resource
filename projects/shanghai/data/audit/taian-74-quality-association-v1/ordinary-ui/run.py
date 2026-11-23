"""Run, verify and assemble the three independent ordinary checks on each device."""
from pathlib import Path
import hashlib, os, json, subprocess, sys
from datetime import datetime, timezone
root=Path(os.environ['ORDINARY_OUTPUT']).absolute()
here=Path(__file__).absolute().parent
def read(p): return json.loads(p.read_bytes())
def write(p,value): p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def attach(p,target):
    target.parent.mkdir(exist_ok=True,parents=True)
    if not target.exists():os.link(p,target)
    assert sha(p)==sha(target)
volume=Path(os.environ['ORDINARY_SAVE_VOLUME']) if os.environ.get('ORDINARY_SAVE_VOLUME') else root.parent / 'stored-downloads'
saved_volume=volume/root.name/'accepted-files'
saved_volume.mkdir(parents=True,exist_ok=True)
if not (root/'saved').exists():(root/'saved').symlink_to(saved_volume)
assert (root/'saved').stat().st_dev==saved_volume.stat().st_dev
records=[]; runs=[];bound=None
by_device={'desktop':{},'phone':{}}
batches=('poses-00-03','poses-03-06','poses-06-08','poses-08-10')
sections=('files','gallery',*batches,'lod')
for section in sections:
    for device,segments in by_device.items():
        stage='cameras' if section in batches else section
        base=root/(device+'-'+section)
        base.mkdir(parents=True,exist_ok=True)
        receipt=None
        for n in range(1,9):
            out=base/str(n)
            closed=out/'closed.json';report=out/'report.json'
            if not closed.exists():
                out.mkdir(parents=True,exist_ok=True)
                env=dict(os.environ,ORDINARY_DEVICE=device,ORDINARY_STAGE=stage,ORDINARY_OUTPUT=str(out))
                if section in batches:
                    _,a,b=section.split('-')
                    env['ORDINARY_CAMERA_LIMITS']=str(int(a))+','+str(int(b))
                with open('/tmp/shanghai-standalone-viewer.lock','a') as slot:
                    __import__('fcntl').flock(slot,__import__('fcntl').LOCK_EX)
                    subprocess.run([sys.executable,'-Bu',here/'physical-stage.py'],env=env)
            if not closed.exists():continue
            c=read(closed)
            if c['exit']==0 and len(c['chrome_pids'])==1 and not c['remaining'] and report.is_file() and c['report_sha256']==sha(report):
                r=read(report)
                if not (r['passed'] and r['stage']==stage and r['runs'][0]['device']==device):continue
                source='test-downloads.cjs' if stage=='files' else 'test.cjs' if stage=='gallery' else 'test-direct.cjs'
                assert r['scriptSHA256']==sha(here/source)
                if source!='test.cjs':assert r['devtools_sha256']==sha(here/'phone-devtools.cjs')
                if bound is None:bound=r['bound']
                assert r['bound']==bound
                receipt={'device':device,'stage':stage,'attempt':n,'closed':c,'report_sha256':sha(report),'closed_sha256':sha(closed),'report':r}
                receipt['section']=section
                if section in batches:
                    assert r['camera_limits']==[int(x)for x in section.split('-')[1:]]
                    assert len(r['runs'][0]['screens'])==r['camera_limits'][1]-r['camera_limits'][0]
                records.append(receipt);segments[section]=r['runs'][0]
                if stage=='cameras':
                    for shot in r['runs'][0]['screens']:attach(out/shot['filename'],root/shot['filename'])
                if stage=='files':
                    for item in [*r['runs'][0]['downloads'].values(),r['runs'][0]['sourceArchive']]:
                        f=item.get('filename',item.get('file'));attach(out/'saved'/device/f,root/'saved'/device/f)
                break
        if receipt is None:raise RuntimeError((device,stage,'no complete physical session'))
for device,segments in by_device.items():
    g=segments['gallery'];d=segments['files'];levels=segments['lod']
    photos=[segments[k]for k in batches]
    c=dict(photos[0],screens=[shot for session in photos for shot in session['screens']],
           closed=all(x['closed'] for x in photos),passed=all(x['passed']for x in photos),
           errors=[e for x in photos for e in x['errors']],camera_processes=len(photos))
    assert len(g['registeredImages'])==4 and len(c['screens'])==len({v['camera'] for v in c['screens']}) and len(c['screens'])==10 and len(d['downloads'])==7 and d['sourceArchive']['saveAsVerified']
    assert all(v['closed'] and v['passed'] and not v['errors'] for v in (g,c,d,levels))
    assert levels['two_current_levels'] and (device=='phone' or levels['wheel_automatic'])
    runs.append(dict(c,two_current_levels=True,wheel_automatic=levels.get('wheel_automatic',False),registeredImages=g['registeredImages'],galleryContext=g['galleryContext'],gallery_closed=g['closed'],downloads=d['downloads'],sourceArchive=d['sourceArchive'],sessions={s:True for s in segments}))
stages=root/'physical-stages.json';write(stages,records)
final=root/'report.json';write(final,{'id':r['id'],'page':r['page'],'scriptSHA256':sha(here/'test.cjs'),'bound':bound,'runs':runs,'passed':True,'physical_stages_sha256':sha(stages),'direct_phone_driver_sha256':sha(here/'test-direct.cjs'),'capture_method':'Seven sequential browsers per device: image gallery, four camera batches (all ten camera buttons), near/far and actual file downloads.'})
pids=[p for row in records for p in row['closed']['chrome_pids']];assert len(set(pids))==14
write(root/'closed.json',{'exit':0,'node_pids':[row['closed']['node'] for row in records],'chrome_pids':pids,'remaining':[],'report_sha256':sha(final),'physical_stages_sha256':sha(stages),'started':records[0]['closed']['started'],'finished':records[-1]['closed']['finished']})
