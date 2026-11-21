"""Check original 226 physical attempts and successful replacements in the publication payload."""
from pathlib import Path
import hashlib,json,re
from datetime import datetime
W=Path('/tmp/shanghai-main-226/final-map-31226')
PHASES={'before01-preload-enospc':'before','phone01-disappeared-materialized-root':'phone','phone02-unix-socket-length':'phone'}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def data(p):return json.loads(p.read_bytes())
def files(folder):return {p.name:sha(p) for p in folder.iterdir() if p.is_file()}
def named_report(phase):return ('control' if phase=='before' else 'main')+'-browser.json'
def check_pair(label,old,good):
 phase=PHASES[label];failed=data(old/'process.json');passed=data(good/'process.json')
 assert failed['phase']==passed['phase']==phase and failed['exit_code']==1 and passed['exit_code']==0
 assert failed['remaining_children']==failed['remaining_chromium']==passed['remaining_children']==passed['remaining_chromium']==[]
 assert passed['node_closed'] and passed['node_pids'] and passed['chromium_pids']
 assert datetime.fromisoformat(failed['finished'])<=datetime.fromisoformat(passed['started'])
 report=good/named_report(phase);result=data(report)
 assert sha(report)==passed['report_sha256'] and result['completed'] and result['phase']==phase
 assert result['scriptSha256']==sha(good/'check-map-stages.cjs') and result['screenshots']
 for view in result['screenshots']:
  img=good/Path(view['file']).name
  assert img.stat().st_size==view['bytes'] and sha(img)==view['sha256']
 returned={}
 if label=='before01-preload-enospc':
  assert not failed['node_pids'] and not failed['chromium_pids'] and not failed['node_closed'] and failed['report_sha256'] is None
  assert '[Errno 28] No space left on device' in (old/'wait-and-run.log').read_text()
  assert not list(old.glob('*.png')) and not (old/named_report(phase)).exists()
 elif label=='phone01-disappeared-materialized-root':
  partial=old/named_report(phase);initial=data(partial)
  assert sha(partial)==failed['report_sha256'] and failed['node_closed'] and failed['node_pids'] and failed['chromium_pids'] and not initial['completed']
  assert all(initial[k]==result[k]for k in ('id','mode','phase','server','scriptSha256','caseSha256','catalog'))
  assert len(initial['screenshots'])==2
  for v in initial['screenshots']:
   pic=old/Path(v['file']).name;assert sha(pic)==v['sha256'] and pic.stat().st_size==v['bytes']
  assert 'ENOENT' in (old/'phone.log').read_text() and 'candidate-city-integrations.json' in (old/'phone.log').read_text()
 else:
  log=(old/'phone.log').read_text();launched=re.search(r'<launched> pid=(\d+)',log);assert launched
  assert 'Socket path too long' in log and 'signal=SIGABRT' in log and failed['node_closed'] and failed['node_pids'] and not failed['chromium_pids']
  assert failed['report_sha256'] is None and not list(old.glob('*.png')) and not (old/named_report(phase)).exists()
  returned={'browser_pid_in_log':int(launched.group(1)),'browser_exit_signal':'SIGABRT'}
 return dict(phase=phase,failed_exit=1,replacement_exit=0,missing_report=failed['report_sha256'] is None,**returned)
def verify(audit,n,names):
 assert n==226
 audit=Path(audit);city=audit/'city-31226';book=city/'archived-browser-attempts.json';listing=data(book)
 assert listing['order']==226 and listing['previous_order']==225 and listing['previous_release_sha256']==sha(Path('/tmp/gaoyang225/225-map-slot-released.json'))
 assert set(PHASES)==set(listing['attempts'])
 verified=set()
 for label,row in listing['attempts'].items():
  old=city/'attempts'/label;good=city/'successful-reruns'/PHASES[label]
  assert row['observation']==check_pair(label,old,good)
  assert files(old)==row['files'] and files(good)==row['replacement_files']
  for p in [*old.iterdir(),*good.iterdir()]:
   assert p.relative_to(audit).as_posix() in names
   if p.suffix=='.json' and (p.parent==old and p.name in ('process.json','main-browser.json')):verified.add(p)
 assert book.relative_to(audit).as_posix() in names
 return verified
