"""Verify each original 229 attempt against its origin and the completed phase."""
from pathlib import Path
from hashlib import file_digest
from datetime import datetime
import json, re
HERE=Path(__file__).parent
WORK=Path('/tmp/shanghai-main-229/final-map-31229')
HISTORY=Path('/workspace/.e-resource-recovery/history/replay229')
PREVIOUS=Path('/tmp/shanghai-main-228/228-map-slot-released.json')
def sha(path):
    with Path(path).open('rb') as f:return file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def origins():
    labels={}
    for parent in (WORK,HISTORY):
        for d in parent.iterdir():
            m=re.fullmatch(r'(before|phone|desktop|architecture|mouse|touch|distant)(\d\d)-[a-z0-9-]+',d.name)
            if m and d.is_dir():labels.setdefault(d.name,{})[str(parent)]=d
    return labels
def listed(d):
    return {f.name:sha(f) for f in d.iterdir() if f.is_file()}
def report_name(phase):return 'control-browser.json' if phase=='before' else 'main-browser.json'
def validate_attempt(label,folder):
    phase=re.match(r'^[a-z]+',label)[0]
    raw=folder/'process.json'
    if label=='before01-source-materialization':
        trace=read(folder/'physical.json')
        assert raw.stat().st_size==0 and trace['empty_receipt_bytes']==0 and trace['remaining_children']==[]
        assert trace['wait_status']==256 and trace['exit_code']==1 and trace['proc_stat'].startswith(str(trace['wrapper_pid'])+' (python) Z')
        assert 'No Node or Chromium launch was observed.' in trace['actual_state']
        assert not (folder/report_name(phase)).exists()
        return {'phase':phase,'exit_code':1,'node_observed':False,'report':False}
    finish=read(raw)
    assert finish['phase']==phase and finish['exit_code']!=0 and finish['remaining_children']==finish['remaining_chromium']==[]
    assert datetime.fromisoformat(finish['started'])<=datetime.fromisoformat(finish['finished'])
    p=folder/report_name(phase)
    if not p.exists():
        assert finish['report_sha256'] is None
        assert label=='before02-no-fcntl-binding' and not finish['node_closed'] and not finish['chromium_pids']
        assert "no attribute 'F_ADD_SEALS'" in (folder/'physical-driver.log').read_text()
        return {'phase':phase,'exit_code':finish['exit_code'],'node_observed':False,'report':False}
    assert finish['node_closed'] and finish['node_pids'] and finish['chromium_pids'] and finish['report_sha256']==sha(p)
    r=read(p);assert r['id']=='putuo-central-mint-main-portico' and not r['completed'] and r.get('phase',phase)==phase
    assert r['scriptSha256']==sha(folder/'check-map-stages.cjs')
    assert r['caseSha256']==sha(Path('/workspace/e-resource/projects/shanghai/data/audit/central-mint-main-portico-v1/map-case.json'))
    assert r['catalog']['count']==(265 if phase=='before' else 266)
    for pic in r['screenshots']:
        f=folder/Path(pic['file']).name;assert f.stat().st_size==pic['bytes'] and sha(f)==pic['sha256']
    return {'phase':phase,'exit_code':finish['exit_code'],'node_observed':True,'report':True,'reported_frames':len(r['screenshots'])}
def validate_replacement(phase,folder):
    rec=read(folder/'process.json');r=folder/report_name(phase);obj=read(r)
    assert rec['phase']==phase and rec['exit_code']==0 and rec['node_pids'] and rec['node_closed'] and rec['chromium_pids']
    assert rec['remaining_children']==rec['remaining_chromium']==[] and rec['report_sha256']==sha(r)
    assert obj['completed'] and obj['phase']==phase and obj['id']=='putuo-central-mint-main-portico' and obj['scriptSha256']==sha(folder/'check-map-stages.cjs')
    assert obj['catalog']['count']==(265 if phase=='before' else 266)
    for pic in obj['screenshots']:
        p=folder/Path(pic['file']).name;assert sha(p)==pic['sha256'] and p.stat().st_size==pic['bytes']
    return obj
def verify(audit,n,names):
    assert n==229;root=Path(audit);city=root/'city-31229';manifest=city/'archived-browser-attempts.json';book=read(manifest)
    assert book['order']==229 and book['previous_order']==228 and book['previous_release_sha256']==sha(PREVIOUS)
    assert set(book['attempts'])==set(origins()) and manifest.relative_to(root).as_posix() in names
    allowed=set()
    for label,row in book['attempts'].items():
        sources=origins()[label];original={}
        for d in sources.values():original.update(listed(d))
        fixed=city/'attempts'/label
        assert listed(fixed)==original==row['files']
        observed=validate_attempt(label,fixed);assert observed==row['observation']
        phase=observed['phase'];good=city/'successful-reruns'/phase;validate_replacement(phase,good)
        assert listed(good)==row['replacement_files']
        if observed['node_observed']:
            assert datetime.fromisoformat(read(fixed/'process.json')['finished'])<=datetime.fromisoformat(read(good/'process.json')['started'])
            if observed['report']:
                assert read(fixed/report_name(phase))['catalog']==read(good/report_name(phase))['catalog']
        for f in [*fixed.iterdir(),*good.iterdir()]:
            assert f.relative_to(root).as_posix() in names
            if f.parent==fixed and (f.name in ('process.json','physical.json',report_name(phase)) or f.stat().st_size==0):allowed.add(f)
    return allowed
