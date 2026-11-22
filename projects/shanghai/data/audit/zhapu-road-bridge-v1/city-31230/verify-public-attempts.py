"""Validate the signed originals before permitting failed browser records in the public archive."""
from pathlib import Path
from hashlib import file_digest
import json,runpy
WORK=Path('/tmp/shanghai-main-230')
HISTORY_SHA='7bbe9b1762c239a84393063f1b84988bfe6aff70627813c2734d450b58b5111f'
def sha(path):
    with path.open('rb')as f:return file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def verify(audit,n,names):
    assert n==230
    root=Path(audit);city=root/'city-31230';hist=WORK/'verify-attempts.py'
    assert sha(hist)==HISTORY_SHA==sha(city/'verify-attempts.py')
    material=runpy.run_path(str(hist))['history'](WORK)
    index=city/'attempts/index.json'
    assert material==read(index) and index.relative_to(root).as_posix() in names
    assert sha(index)==read(city/'slot-released.json')['failed_attempts_sha256']
    accepted=set();expect={index}
    for attempt in material['attempts']:
        phase=attempt['phase'];captured=city/'attempts'/phase/attempt['attempt']
        closed=read(captured/'closed.json')
        report_file='real-city.json' if phase.startswith('walk') else 'viewer.json' if phase=='standalone' else 'report.json'
        replacement=city/'sessions'/phase
        assert sha(replacement/'closed.json')==attempt['successful_retry_exit_sha256']
        assert sha(replacement/report_file)==attempt['successful_retry_report_sha256']
        for rel,properties in attempt['files'].items():
            f=city/rel
            assert f.is_relative_to(captured) and f.relative_to(root).as_posix() in names
            assert f.stat().st_size==properties['bytes'] and sha(f)==properties['sha256']
            expect.add(f)
            if f.parent==captured and f.name in ('closed.json',report_file):
                accepted.add(f)
            elif f.parent==captured and f.name=='run.log' and f.stat().st_size==0:
                accepted.add(f)
            elif f.parent.parent==captured and f.parent.name.startswith('component-') and f.name in ('process.json','real-city.json'):
                proc=f.parent/'process.json'
                if proc.is_file():
                    stage=read(proc)
                    assert stage['driver_sha256']==closed['driver_sha256'] and stage['node']>1
                    if stage['exit']!=0:
                        if f.name=='real-city.json':assert sha(f)==stage['report_sha256']
                        accepted.add(f)
    assert {f for f in (city/'attempts').rglob('*') if f.is_file()}==expect
    return accepted
