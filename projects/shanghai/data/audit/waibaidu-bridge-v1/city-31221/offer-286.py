from pathlib import Path
import hashlib,json,subprocess,sys
w=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=w/'offer-286-before-phone-runtime-ab186ff9ef25edb92e1c48cbebedd92a27322bd058d90c905f4eb5706f75a445.py'
assert sha(old)=='ab186ff9ef25edb92e1c48cbebedd92a27322bd058d90c905f4eb5706f75a445'
subprocess.run([sys.executable,'-B',old,*sys.argv[1:]],check=True)
if sys.argv[1:]==['phone']:
 source=w/'sessions/phone/closed.json';program=Path('/tmp/york-sichuan286/mapping/after-221-phone.py')
 assert sha(program)=='9e4de1bc9f332057ed391a9dce3a63c353e319438aea71aacd716fdc6a389ccd'
 subprocess.run([sys.executable,'-B',program,source],check=True)
 res=program.parent/'221-phone-runtime-closed.json';d=json.loads(res.read_bytes())
 assert d['host_sha256']==sha(source) and d['host_report_sha256']==sha(source.parent/'report.json') and d['remaining']==[]
 assert d['pid']>0 and type(d['exit_code']) is int and sha(Path(d['log']))==d['log_sha256']
