"""Resume the unchanged 258 city sequence once the earlier independent exhibition exits."""
import hashlib,json,os,sys
from pathlib import Path
w=Path(__file__).parent
def load(path):
    return json.loads(Path(path).read_bytes())
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
supervisor=load(w/'supervisor-recovered.json')
for name,value in supervisor['files'].items():
    assert sha(w/name)==value,name
held=supervisor['predecessor_development']
out=load(held['return'])
terminal=Path(supervisor['predecessor'])
host=terminal.parent/'evidence/desktop/closed.json'
closed=load(host)
assert out['order']==436 and out['host']==257
assert out['host_sha256']==sha(host) and out['host_report_sha256']==closed['report_sha256']==sha(closed['report'])
assert out['previous_sha256']==sha(terminal) and load(terminal)['passed']
assert out['all_children_exited'] and out['remaining_children']==[]
physical=Path(out['physical'])
assert physical.samefile(Path(held['return']).with_name('physical.json')) and sha(physical)==out['physical_sha256']
result=load(physical)
assert result['exit_code']==out['exit_code'] and result['passed']==out['passed']
assert result['all_children_exited'] and result['remaining_children']==[]
for name,value in result['reports'].items():
    assert sha(physical.parent/name)==value,name
os.execv(sys.executable,[sys.executable,'-Bu',str(w/'sequence-recovered.py')])
