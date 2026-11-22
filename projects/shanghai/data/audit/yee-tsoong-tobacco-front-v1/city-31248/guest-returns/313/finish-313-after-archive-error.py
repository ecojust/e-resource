"""Archive a completed viewer process using its signed screenshots and download counters."""
from pathlib import Path
import hashlib, json, os, shutil
host=Path('/tmp/shanghai-main-248/formal-31248')
w=Path('/tmp/kangding313');hand=w/'handoff'
project=Path('/workspace/e-resource/projects/shanghai');ident='jingan-kangding-garden-central-portico'
assets=project/'assets/models/candidates'/ident;target=project/'data/audit/kangding-central-portico-v1/standalone-31313'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def keep(src,dst):
    if not dst.exists():
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    assert sha(src)==sha(dst)
error=hand/'viewer-2329953.log'
assert 'No space left on device' in error.read_text() and 'standalone-31313' in error.read_text()
denial=read(hand/'viewer-deferred.json');row=read(hand/'viewer-most-recent-exit.json');assert denial['physical_exit']==row and denial['attempt_exit_code']==1
assert row['wrapper_closed'] and row['exit_code']==row['exit']==0 and row['remaining']==[]
attempt=Path(row['attempt']);assert read(attempt/'physical-exit.json')==row
assert row['host_receipt_sha256']==sha(host/'isolated-evidence/mobile-pin/closed.json')
v=read(attempt/'viewer.json');confirmed=read(attempt/'three-http-inputs.json');manifest=read(assets/'manifest.json')
assert v['base']=='http://127.0.0.1:31313/' and v['id']==ident and v['passed'] and not v['pageErrors']
assert v['scriptSHA256']==sha(hand/'six-view-download.cjs') and v['manifestSHA256']==sha(assets/'manifest.json')==confirmed['inputs'][f'assets/models/candidates/{ident}/manifest.json']
assert len(v['views'])==6 and len(v['downloads'])==4
target.mkdir(exist_ok=True)
for item in v['views']:
    f=attempt/item['filename'];assert sha(f)==item['sha256'];keep(f,target/f.name)
for role,item in manifest['assets'].items():
    record=v['downloads'][role];assert all(record[k]==item[k] for k in ('file','sha256','bytes'))
    assert sha(assets/item['file'])==record['sha256'] and record['saved_as']=='observed-'+item['file']
for name in ('viewer.json','three-http-inputs.json'):keep(attempt/name,target/name)
chrome=[int(pid) for pid,name in row['observed_processes'].items() if name in ('chrome','chromium')];assert chrome
result={**row,'passed':True,'all_processes_closed':True,'node':row['wrapper_pid'],'chromium_pids':chrome,'remaining_chromium':[],'views':6,'downloads':4,'receipt_sha256':sha(attempt/'viewer.json'),'report_sha256':sha(target/'viewer.json'),'report':str(target/'viewer.json'),'signed_source_report':str(target/'three-http-inputs.json'),'signed_source_sha256':sha(target/'three-http-inputs.json'),'assets':manifest['assets'],'archive_failure_sha256':sha(error),'archive_recovered_from_original_exit_sha256':sha(attempt/'physical-exit.json')}
out=w/'viewer-closed.json'
if out.exists():assert read(out)==result
else:out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(sha(out))
