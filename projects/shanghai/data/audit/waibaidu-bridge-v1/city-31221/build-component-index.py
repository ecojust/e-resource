"""Associate incomplete camera components and re-used completed captures with actual process receipts."""
from pathlib import Path
import json,hashlib,os
w=Path(__file__).parent
def sig(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def link(path):return dict(path=str(path.relative_to(w)),sha256=sig(path))
def build():
 attempts=[]
 for old in sorted((w/'attempts').glob('*/*/component-*/process.json')):
  oldproc=read(old);stage=old.parents[1].name;section=oldproc['section']
  if oldproc['exit']==0:continue
  assert oldproc['node']>0 and oldproc['finished'] and old.parent.name=='component-'+section
  oldreport=old.parent/'real-city.json';assert sig(oldreport)==oldproc['report_sha256'] and not read(oldreport).get('passed')
  earlier=old.parents[1]/'closed.json';later=w/'sessions'/stage/'closed.json'
  for item in (earlier,later):
   cl=read(item);assert cl['phase']==stage and cl['node_closed'] and cl['remaining']==[]
  assert read(earlier)['exit']!=0 and read(later)['exit']==0
  after=w/'sessions'/stage/('component-'+section)/'process.json';newproc=read(after);newrep=after.parent/'real-city.json'
  assert oldproc['finished']<=newproc['started'] and newproc['node']>0 and newproc['exit']==0 and newproc['section']==section and sig(newrep)==newproc['report_sha256']
  newer=read(newrep);assert newer['passed'] and newer['closed']
  for v in newer['cases']:assert v['sha256']==sig(newrep.parent/v['file'])
  attempts.append(dict(phase=stage,component=section,old_host=link(earlier),old_process=link(old),old_report=link(oldreport),replacement_host=link(later),replacement_process=link(after),replacement_report=link(newrep)))
 reused=[]
 for mark in sorted((w/'attempts').glob('*/*/component-*/process.json')):
  proc=read(mark);stage=mark.parents[1].name;section=proc['section']
  after=w/'sessions'/stage/('component-'+section)/'process.json'
  if proc['exit']!=0 or not after.exists() or sig(mark)!=sig(after):continue
  oldreport=mark.parent/'real-city.json';newreport=after.parent/'real-city.json'
  assert sig(oldreport)==proc['report_sha256']==sig(newreport) and read(newreport)['passed']
  reused.append(dict(phase=stage,component=section,old_process=link(mark),retained_process=link(after),retained_report=link(newreport)))
 doc=dict(order=221,components=attempts,reused=reused);dest=w/'archived-walk-components.json';tmp=dest.with_suffix('.partial');tmp.write_text(json.dumps(doc,indent=2)+'\n');os.replace(tmp,dest);return dest
if __name__=='__main__':print(build())
