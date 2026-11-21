"""Preserve the exact earlier reports and certify their matching successful repeat."""
from hashlib import sha256
from pathlib import Path
import json, shutil
w=Path(__file__).parent
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/yan-tongchun-residence-v1')
out=audit/'final-map-31188'
read=lambda f:json.loads(f.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
def normalized(raw,path,failed_exit=None):
    receipt=read(raw)
    assert receipt.get('browserClosed') or failed_exit == 1
    info=dict(id=receipt['id'],passed=receipt['completed'],browser_closed=receipt.get('browserClosed'),
              base=receipt['site'],mode=receipt['mode'],captures=receipt['views'],
              exact_report=str(raw.relative_to(audit)),exact_report_sha256=digest(raw),
              source_catalog_sha256=receipt['catalog']['sha256'],map_case_sha256=receipt['caseSha256'],
              contract_sha256=receipt['contractSha256'],signed_release_sha256=receipt['snapshotSha256'],
              exit_feedback=receipt.get('failure',None), process_exit=failed_exit)
    path.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    return info
attempts=[]
for failed in sorted(w.glob('attempt-*-*-crash')):
    phase='before' if (failed/'before/before.json').exists() else ('distant' if (failed/'distant/after.json').exists() else 'desktop')
    successful=out/('before.json' if phase=='before' else phase+'-browser.json')
    valid=out/(phase+'-passing-receipt.json')
    passing=normalized(successful,valid)
    assert passing['passed'] and passing['captures']
    original=failed/phase/('before.json' if phase=='before' else 'after.json')
    log=failed/(phase+'.log')
    target=out/failed.name;target.mkdir(exist_ok=True)
    raw=target/'original-browser.json';shutil.copy2(original,raw);assert digest(original)==digest(raw)
    stdout=target/(phase+'.log');shutil.copy2(log,stdout);assert digest(log)==digest(stdout)
    js=target/'check-independent-city.cjs';shutil.copy2(failed/js.name,js)
    assert digest(js)==read(raw)['scriptSha256']
    norm=target/'failed-receipt.json';earlier=normalized(raw,norm,int((failed/(phase+'.exit')).read_text()))
    assert not earlier['passed'] and (earlier['exit_feedback'] or 'Page crashed' in log.read_text())
    for field in ('id','base','mode','source_catalog_sha256','map_case_sha256','contract_sha256','signed_release_sha256'):
        assert earlier[field]==passing[field],field
    for view in earlier['captures']:
        image=failed/phase/view['file'];dest=target/image.name
        shutil.copy2(image,dest);assert digest(dest)==view['sha256']
    attempts.append(dict(report=str(norm.relative_to(audit)),sha256=digest(norm),superseded_by=str(valid.relative_to(audit)),superseded_by_sha256=digest(valid),
                         stdout={str(stdout.relative_to(audit)):digest(stdout)},original_report=str(raw.relative_to(audit)),original_sha256=digest(raw)))
assert attempts
(audit/'archived-browser-attempts.json').write_text(json.dumps(dict(model=passing['id'],attempts=attempts),ensure_ascii=False,indent=2)+'\n')
