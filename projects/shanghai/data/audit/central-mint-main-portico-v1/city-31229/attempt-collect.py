"""Collect only actual map attempts and their matched real 229 replacements."""
from pathlib import Path
import os,shutil,json,sys,runpy
api=runpy.run_path(str(Path(__file__).with_name('verify.py')))
sha=api['sha'];read=api['read'];W=api['WORK'];H=api['HISTORY']
def collect(audit):
    root=Path(audit);city=root/'city-31229';book={};names=set()
    def keep(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():
            try:os.link(src.resolve(strict=True),dst)
            except OSError:shutil.copy2(src,dst)
        assert sha(src)==sha(dst)
        names.add(dst.relative_to(root).as_posix())
    for label,locations in api['origins']().items():
        fixed=city/'attempts'/label
        for source in locations.values():
            for f in source.iterdir():
                if f.is_file():keep(f,fixed/f.name)
        observed=api['validate_attempt'](label,fixed);phase=observed['phase'];good=city/'successful-reruns'/phase
        p=W/phase/api['report_name'](phase);obj=read(p);driver=None
        for f in [W/'check-map-stages.cjs',*H.glob('check*.cjs'),*(f for origins in api['origins']().values() for v in origins.values() for f in (v/'check-map-stages.cjs',v/'new-checker.cjs'))]:
            if f.is_file() and sha(f)==obj['scriptSha256']:driver=f;break
        assert driver,'Original successful phase driver is required'
        keep(driver,good/'check-map-stages.cjs')
        for f in [p,p.parent/'process.json',*[p.parent/Path(x['file']).name for x in obj['screenshots']]]:keep(f,good/f.name)
        api['validate_replacement'](phase,good)
        book[label]=dict(observation=observed,files=api['listed'](fixed),replacement_files=api['listed'](good))
    path=city/'archived-browser-attempts.json';path.write_text(json.dumps(dict(order=229,previous_order=228,previous_release_sha256=sha(api['PREVIOUS']),attempts=book),indent=2)+'\n');names.add(path.relative_to(root).as_posix())
    api['verify'](root,229,names);return names
if __name__=='__main__':print(json.dumps(sorted(collect(Path(sys.argv[1])))))
