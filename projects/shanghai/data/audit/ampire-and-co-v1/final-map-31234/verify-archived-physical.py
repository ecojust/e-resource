"""Preserve exact failed browser records and bind them to physically closed repetitions."""
from pathlib import Path
from hashlib import file_digest
import json,os,shutil

WORK=Path('/tmp/shanghai-main-234/final-map-31234')
DEST='final-map-31234'
def digest(f):
    with f.open('rb') as src:
        return file_digest(src,'sha256').hexdigest()
def read(f):
    return json.loads(f.read_bytes())
def closure(f,expected_phase,success):
    v=read(f)
    assert v['phase']==expected_phase and v['node_closed'] and v['node_pids'] and v['chromium_pids']
    assert (v['exit_code']==0)==success and v['remaining_children']==v['remaining_chromium']==[]
    return v
def index():
    rows={}
    for attempt in sorted(WORK.glob('failed-*-*')):
        prefix,phase,number=attempt.name.split('-')
        assert prefix=='failed' and number.isdigit()
        old=closure(attempt/phase/'process.json',phase,False)
        final=closure(WORK/phase/'process.json',phase,True)
        child_exit=int((attempt/(phase+'.exit')).read_text())
        # run.py propagates the signed subprocess returncode via SystemExit, whose
        # physical Python process exposes the low eight bits to sequence.py.
        assert -127<=child_exit<=255 and child_exit%256==old['exit_code']
        if child_exit<0:
            assert 'raise SystemExit(r.returncode)' in (attempt/'run.py').read_text()
        assert old['finished']<=final['started']
        name='control-browser.json' if phase=='before' else 'main-browser.json'
        retry=WORK/phase/name
        report=read(retry)
        assert digest(retry)==final['report_sha256'] and report['completed'] and report['phase']==phase
        assert report['id']=='huangpu-ampire-and-co-building' and not report['errors'] and not report['failed']
        original=attempt/phase/name
        if old['report_sha256']:
            assert digest(original)==old['report_sha256']
            failed=read(original)
            assert not failed['completed'] and digest(attempt/'check-map-stages.cjs')==failed['scriptSha256']
            for key in ['id','phase','server','mode','caseSha256','sourceCommit','catalog','bindings']:
                assert failed[key]==report[key],(phase,key)
            for shot in failed['screenshots']:
                assert digest(original.parent/shot['file'])==shot['sha256']
        else:
            assert not original.exists() and attempt.name=='failed-before-02'
            assert b'No live page' in (attempt/'before.log').read_bytes()
        files={str(f.relative_to(attempt)):{'bytes':f.stat().st_size,'sha256':digest(f)} for f in sorted(attempt.rglob('*')) if f.is_file()}
        rows[attempt.name]=dict(phase=phase,exit_code=old['exit_code'],files=files,success_report=name,success_report_sha256=digest(retry),success_exit_sha256=digest(WORK/phase/'process.json'))
    assert {'failed-before-01','failed-before-02'}<=set(rows)
    return dict(order=234,attempts=rows)
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():
        try:os.link(src,dst)
        except OSError:shutil.copyfile(src,dst)
    assert digest(src)==digest(dst)
def materialize(audit):
    base=Path(audit)/DEST/'failed-browser-attempts';data=index()
    for label,row in data['attempts'].items():
        for name in row['files']:
            copy(WORK/label/name,base/label/name)
        log=base/label/(row['phase']+'.log')
        if any(l.endswith((b' ',b'\t')) for l in log.read_bytes().splitlines()):
            (log.parent/'.gitattributes').write_text(log.name+' -whitespace\n')
    encoded=(json.dumps(data,indent=2)+'\n').encode()
    (base/'index.json').write_bytes(encoded)
    return digest(base/'index.json')
def verify(audit,order,names):
    audit=Path(audit).resolve();base=audit/DEST/'failed-browser-attempts';idx=base/'index.json'
    assert order==234 and idx.relative_to(audit).as_posix() in names
    data=index()
    assert data==read(idx) and digest(idx)==read(audit/DEST/'slot-released.json')['failed_attempts_sha256']
    expected={idx}; accepted=set()
    for label,row in data['attempts'].items():
        phase=row['phase'];dst=base/label;passed=audit/DEST/phase
        assert digest(passed/row['success_report'])==row['success_report_sha256'] and digest(passed/'closed.json')==row['success_exit_sha256']
        for name,fields in row['files'].items():
            f=dst/name
            assert f.resolve().is_relative_to(dst) and f.relative_to(audit).as_posix() in names
            assert f.stat().st_size==fields['bytes'] and digest(f)==fields['sha256']
            expected.add(f)
            if name in (phase+'/process.json',phase+'/'+row['success_report'],phase+'.log'):
                accepted.add(f)
        att=dst/'.gitattributes';log=dst/(phase+'.log')
        if any(l.endswith((b' ',b'\t')) for l in log.read_bytes().splitlines()):
            assert att.read_bytes()==(log.name+' -whitespace\n').encode()
            expected.add(att)
    assert expected=={p for p in base.rglob('*') if p.is_file()}
    return accepted
