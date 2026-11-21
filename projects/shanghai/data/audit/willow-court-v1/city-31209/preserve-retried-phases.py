"""Bind unaltered unsuccessful city runs to the fully closed repeat on that same signed map."""
from pathlib import Path
from hashlib import file_digest
import json,os,shutil
w=Path(__file__).resolve().parent
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/willow-court-v1')
city=audit/'city-31209'
ident='xuhui-willow-court'
def digest(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
    if p.exists():assert p.read_bytes()==data;return
    temp=p.with_suffix('.tmp');temp.write_bytes(data);temp.replace(p)
def save(source,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    if not dest.exists():
        try:os.link(source,dest)
        except OSError:shutil.copyfile(source,dest)
    assert digest(source)==digest(dest)
def outcome(closure,browser):
    c=read(closure);b=read(browser)
    assert c['phase']==b['phase'] and c['report_sha256']==digest(browser)
    assert c['cdp_closed'] and not c['remaining_chromium'] and c['observed_chromium_pid_and_starttime']
    passed=c['exit_code']==0 and b['completed']
    return {'id':ident,'mode':b['phase'],'base':b['server'],'passed':bool(passed),'browser_closed':True,
            'exit_code':c['exit_code'],'report_sha256':digest(browser),'closure_sha256':digest(closure),'captures':b['screenshots']}
rows=[]
for bad in sorted((w/'isolated-evidence').glob('*-old*/failed-exit.json')):
    phase=read(bad)['phase'];key=phase+('-wide' if '-wide-old' in bad.parent.name else '');final=w/'isolated-evidence'/key;accepted=final/'closed.json'
    original=bad.parent/('control-browser.json'if phase=='control'else'main-browser.json')
    success=final/original.name
    pre=outcome(bad,original);post=outcome(accepted,success)
    assert not pre['passed'] and post['passed'] and pre['base']==post['base'] and post['captures']
    dest=city/'retained-attempts'/bad.parent.name
    for file in bad.parent.iterdir():
        if file.is_file():save(file,dest/file.name)
    program,=[f for f in w.glob('check-willow*.cjs') if digest(f)==read(bad)['source_code_sha256']]
    save(program,dest/program.name)
    for im in post['captures']:assert digest(final/im['file'])==im['sha256']
    assert digest(dest/'node.log')==read(bad)['stdout_sha256']
    old=dest/'outcome.json';new=city/'actual-browser-phases'/(key+'-outcome.json')
    write(old,pre);write(new,post)
    rows.append({'report':str(old.relative_to(audit)),'sha256':digest(old),'superseded_by':str(new.relative_to(audit)),
                 'superseded_by_sha256':digest(new),'stdout':{str((dest/'node.log').relative_to(audit)):digest(dest/'node.log')}})
if rows:write(audit/'archived-browser-attempts.json',{'model':ident,'attempts':rows})
print('retained',len(rows),'unchanged unsuccessful runs')
