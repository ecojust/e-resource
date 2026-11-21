"""Preserve the exact bytes from each physical failure and its successful 226 replacement."""
import os,shutil,sys,json,runpy
from pathlib import Path
api=runpy.run_path(str(Path(__file__).with_name('verify.py')))
W=api['W'];PHASES=api['PHASES'];sha=api['sha']
def collect(audit):
 audit=Path(audit);city=audit/'city-31226'; names=set();records={}
 def keep(src,dst):
  dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():
   try:os.link(src,dst)
   except OSError:shutil.copy2(src,dst)
  assert sha(src)==sha(dst);names.add(dst.relative_to(audit).as_posix())
 for label,phase in PHASES.items():
  old=city/'attempts'/label;good=city/'successful-reruns'/phase
  for f in (W/'attempts'/label).iterdir():
   if f.is_file():keep(f,old/f.name)
  r=W/phase/api['named_report'](phase);raw=api['data'](r)
  for f in [r,r.parent/'process.json',W/'check-map-stages.cjs',*[r.parent/Path(v['file']).name for v in raw['screenshots']]]:keep(f,good/f.name)
  records[label]=dict(files=api['files'](old),replacement_files=api['files'](good),observation=api['check_pair'](label,old,good))
 book=city/'archived-browser-attempts.json';payload=dict(order=226,previous_order=225,previous_release_sha256=sha(Path('/tmp/gaoyang225/225-map-slot-released.json')),attempts=records)
 temp=book.with_suffix('.update');temp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');os.replace(temp,book);names.add(book.relative_to(audit).as_posix())
 api['verify'](audit,226,names);return names
if __name__=='__main__':print(json.dumps(sorted(collect(Path(sys.argv[1])))))
