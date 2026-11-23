"""Verify and archive the ordinary 31265 page's four physical saved downloads and both screens."""
from pathlib import Path
import hashlib, json
def verify(field,save):
    read=lambda p:json.loads(p.read_bytes())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    closed=field/'current-standalone/closed.json';r=read(closed)
    assert r['passed'] and r['order']==265 and r['exit_code']==0 and not r['remaining'] and r['chromium']
    assert r['prior_sha256']==sha(field/'isolated-evidence/distant/closed.json')
    report=Path(r['report']);receipt=Path(r['proof'])
    assert sha(report)==r['report_sha256']==read(receipt)['report_sha256']
    q=read(report);base=read(field/'standalone-originals.json')
    assert q['passed'] and len(q['views'])==4 and q['base']=='http://127.0.0.1:31265/'
    assert q['downloads']==r['downloads'] and set(q['downloads'])=={'raw','full','lod','native'}
    for role,row in q['downloads'].items():
        file=report.parent/'saved'/row['file'];orig=base['downloads'][role]
        assert row['saveAsVerified'] and all(row[k]==orig[k] for k in orig)
        assert file.stat().st_size==row['bytes'] and sha(file)==row['sha256']
    for shot in q['views']:
        f=report.parent/shot['filename'];assert sha(f)==shot['sha256']
        save(f,'standalone/'+f.name)
    for f,name in [(report,'viewer.json'),(receipt,'process.json'),(closed,'closed.json')]:
        save(f,'standalone/'+name)
    return q
