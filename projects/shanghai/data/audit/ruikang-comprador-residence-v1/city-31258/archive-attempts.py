"""Preserve unsuccessful process logs and files under their real names alongside the successful repeat."""
from pathlib import Path
import hashlib,json,os,shutil
W=Path(__file__).parent
A=Path('/workspace/e-resource/projects/shanghai/data/audit/ruikang-comprador-residence-v1')
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():
        try:os.link(src,dst)
        except OSError:shutil.copy2(src,dst)
    assert sha(dst)==sha(src)
def main():
    if not (W/'attempts').exists():return
    city=A/'city-31258'
    ledger=[]
    for trial in sorted((W/'attempts').iterdir()):
        tag=trial.name.split('-')[0]
        assert tag in ('before','phone','desktop')
        name='before.json' if tag=='before' else 'after.json'
        failure=trial/name
        final=city/tag/name
        if not failure.exists():continue
        a,b=(json.loads(p.read_bytes()) for p in (failure,final))
        if a.get('passed') is not False:continue
        assert b['passed'] and b['browser_closed'] and b['captures']
        assert all(a[x]==b[x] for x in ('id','base','mode','catalog','signed_input_sha256'))
        assert sha(trial/'actual-driver.cjs') == a['script_sha256']
        assert sha(final.parent/'actual-driver.cjs') == b['script_sha256']
        dest=city/'attempts'/trial.name
        for f in trial.iterdir():
            if f.is_file() and (f==failure or f.name in ('closed.json','process.log','interrupted.json','actual-driver.cjs') or f.suffix=='.png'):
                put(f,dest/f.name)
        stdout={str(f.relative_to(A)):sha(f) for f in dest.glob('*.log')}
        item={'report':str((dest/name).relative_to(A)),'sha256':sha(failure),'superseded_by':str(final.relative_to(A)),'superseded_by_sha256':sha(final),'stdout':stdout}
        ledger.append(item)
    if ledger:
        target=A/'archived-browser-attempts.json'
        data=(json.dumps({'model':'huangpu-ruikang-comprador-residence','attempts':ledger},ensure_ascii=False,indent=2)+'\n').encode()
        if target.is_file():assert target.read_bytes()==data
        else:target.write_bytes(data)
if __name__=='__main__':main()
