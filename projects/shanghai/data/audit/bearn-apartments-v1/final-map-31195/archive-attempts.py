"""Bind the original unsuccessful browser reports to the same release's successful reruns."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import os

w=Path(__file__).parent
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/bearn-apartments-v1')
out=audit/w.name
def read(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return sha256(p.read_bytes()).hexdigest()
def copy(src,dst):
    if not dst.exists():
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    assert sha(src)==sha(dst)

def normalize(p,exit_file,dst):
    raw=read(p);proc=read(exit_file)
    assert raw['id']=='huangpu-bearn-apartments'
    assert sha(p)==proc['report_sha256']
    closed=proc['exit_code']==0 and proc['node_closed'] and not proc['remaining_children'] and not proc['remaining_chromium']
    assert raw['completed']==closed
    result=dict(id=raw['id'],mode=raw['mode'],base=raw['server'],passed=raw['completed'],browser_closed=closed,
                captures=raw['screenshots'],exact_report=p.relative_to(audit).as_posix(),exact_report_sha256=sha(p),
                catalog_sha256=raw['catalog']['sha256'],case_sha256=raw['caseSha256'],exit_status=proc['exit_code'])
    write(dst,result)
    return result

attempts=[]
for original in sorted((w/'attempts').glob('*/*/*-browser.json')):
    phase=original.parent.name
    phase_dir=original.parent.parent;target=out/'earlier-attempts'/phase_dir.name;target.mkdir(parents=True,exist_ok=True)
    success=out/phase/original.name
    base=target/'original-browser.json';copy(original,base)
    process=target/'physical-exit.json';copy(original.parent/'process.json',process)
    log=target/'browser.log';copy(phase_dir/(phase+'.log'),log)
    script=phase_dir/('check-storefront.cjs' if phase=='clear-shopfront' else 'check-map-stages.cjs')
    if script.is_file():
        copy(script,target/script.name)
        assert sha(script)==read(base)['scriptSha256']
    failed=target/'unsuccessful.json';final=out/phase/'passing-repeat.json'
    old=normalize(base,process,failed);new=normalize(success,out/phase/'process.json',final)
    assert not old['passed'] and new['passed'] and new['captures']
    for k in ['id','mode','base','catalog_sha256','case_sha256']:assert old[k]==new[k],k
    for shot in read(base)['screenshots']:
        pic=original.parent/shot['file'];assert sha(pic)==shot['sha256'];copy(pic,target/pic.name)
    attempts.append(dict(report=failed.relative_to(audit).as_posix(),sha256=sha(failed),
                         superseded_by=final.relative_to(audit).as_posix(),superseded_by_sha256=sha(final),
                         original_report=base.relative_to(audit).as_posix(),original_sha256=sha(base),
                         stdout={log.relative_to(audit).as_posix():sha(log)}))
if attempts:write(audit/'archived-browser-attempts.json',dict(model='huangpu-bearn-apartments',attempts=attempts))
