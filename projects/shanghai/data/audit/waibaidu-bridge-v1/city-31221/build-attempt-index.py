"""Associate each physically closed unsuccessful run with its successful repeat using files relative to the formal session."""
from pathlib import Path
import hashlib,json,os
root=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def build():
 out=[]
 for old in sorted((root/'attempts').glob('*/*/closed.json')):
  prior=read(old);stage=prior['phase'];assert old.parent.name==stage
  name='viewer.json' if stage=='standalone' else 'real-city.json' if stage.startswith('walk-') else 'report.json'
  original=old.parent/name; replacement=root/'sessions'/stage/'closed.json'; newer=replacement.parent/name
  second=read(replacement);final=read(newer);assert final['passed'] and second['exit']==0 and sha(newer)==second['report_sha256']
  assert prior['prior_sha256']==second['prior_sha256'] and prior['finished']<=second['started']
  assert prior['node_closed'] and not prior['remaining'] and (prior['exit'] or not original.is_file() or not read(original).get('passed'))
  ids=dict(closed=old,driver=old.parents[1]/Path(prior['driver']).name, log=old.parent/'run.log',replacement_closed=replacement,replacement_report=newer)
  assert sha(ids['driver'])==prior['driver_sha256']
  if original.is_file():
   assert sha(original)==prior['report_sha256'];ids['report']=original
  else:assert prior['report_sha256'] is None
  entry=dict(phase=stage,actual_exit=prior['exit'],node_closed=prior['node_closed'],remaining=prior['remaining'],report=None,report_sha256=None)
  for k,file in ids.items():
   entry[k]=str(file.relative_to(root));entry[k+'_sha256']=sha(file)
  out.append(entry)
 p=root/'archived-browser-attempts.json';data=(json.dumps(dict(order=221,attempts=out),indent=2)+'\n').encode()
 temp=p.with_suffix('.next');temp.write_bytes(data);os.replace(temp,p)
 return p
if __name__=='__main__':print(build())
