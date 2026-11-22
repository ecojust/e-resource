"""Build and reopen the Zhonghe Cun channelled corner pier after the actual 247 desktop pin."""
from datetime import datetime,timezone
from hashlib import file_digest
from pathlib import Path
import fcntl,json,subprocess,sys
w=Path(__file__).parent
receipt=Path(sys.argv[1])
assert receipt==Path('/tmp/shanghai-main-247/formal-31247/isolated-evidence/desktop-pin/closed.json')
def sha(p):
    with p.open('rb')as source:return file_digest(source,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def now():return datetime.now(timezone.utc).isoformat()
host=read(receipt);report=receipt.with_name('main-browser.json')
assert host['exit_code']==0 and host['node_closed'] and host['node_pid']>0 and host['observed_chromium_pid_and_starttime'] and host['chromium_pids']
assert host['phase']=='desktop-pin' and host['order']==247 and host['cdp_closed'] and host['remaining_chromium']==[] and host['report_sha256']==sha(report)
body=read(report)
assert body.get('passed',body.get('completed')) and not body.get('failure')
returned=w/'247-native-returned.json'
with (w/'actual-native.lock').open('a')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    if returned.exists():
        old=read(returned)
        assert old['host_sha256']==sha(receipt) and old['host_report_sha256']==sha(report) and old['all_children_exited'] and old['remaining_children']==[]
        for phase in old['phases']:
            if phase['physical']:assert sha(Path(phase['physical']))==phase['physical_sha256']
        sys.exit(0)
    from runpy import run_path
    helper=Path('/workspace/.e-resource-recovery/grace/verified-native-prior.py')
    assert sha(helper)=='bc59e775b80a6a5d4328347304126f7ac5be1a5645a3b2c9abb5b7ec5058abe4'
    prior=run_path(str(helper))['inspect'](w,554)
    if prior:
        origin,early=prior
        previous=Path(early['previous'])
        archived=Path('/tmp/shanghai-main-240/fourth-240-river-diagnostic')
        old_host=archived/'closed.json';old_report=archived/'browser.json'
        assert sha(old_host)==early['host_sha256'] and sha(old_report)==read(old_host)['report_sha256']==early['host_report_sha256']
        prior=read(previous);assert sha(previous)==early['previous_sha256']
        assert prior['order']==305 and prior['exit_code']==0 and prior['wrapper_closed']
        assert prior['remaining']==[] and prior['remaining_chromium']==[] and prior['chromium_pids']
        reused=dict(order=554,host=247,phase='desktop-pin',host_sha256=sha(receipt),host_report_sha256=sha(report),
            archived_early_host=str(old_host),archived_early_report=str(old_report),archived_early_host_sha256=sha(old_host),archived_early_report_sha256=sha(old_report),attempted=False,already_completed=True,earlier=str(origin),earlier_sha256=sha(origin),previous_completed_exit=0,
            exit_code=None,passed=True,all_children_exited=True,remaining_children=[],four_assets=early['four_assets'],phases=early['phases'],finished=now())
        temp=returned.with_suffix('.partial');temp.write_text(json.dumps(reused,indent=2)+'\n');temp.replace(returned)
        sys.exit(0)
    source=w/'author-physical.json';author=read(source)
    assert author['passed'] and author['all_children_exited'] and author['remaining_children']==[]
    stages=[];r=Path('/workspace/.e-resource-recovery/grace')
    for name,expected in [('native-changning.py','development-native-closed.json'),('reopen-changning.py','native-audit/reopened-physical.json')]:
        script=r/name;started=now()
        with (w/('247-'+name+'.log')).open('wb')as log:
            child=subprocess.Popen([sys.executable,'-Bu',script,w],stdout=log,stderr=subprocess.STDOUT);code=child.wait()
        physical=w/expected
        stages.append(dict(program_sha256=sha(script),pid=child.pid,started=started,finished=now(),exit_code=code,physical=str(physical)if physical.is_file()else None,physical_sha256=sha(physical)if physical.is_file()else None,log_sha256=sha(Path(log.name))))
        assert not Path('/proc',str(child.pid)).exists()
        if code:break
    complete=dict(order=554,host=247,phase='desktop-pin',host_sha256=sha(receipt),host_report_sha256=sha(report),author_sha256=sha(source),phases=stages,exit_code=code,passed=len(stages)==2 and code==0,all_children_exited=True,remaining_children=[],finished=now())
    temp=returned.with_suffix('.partial');temp.write_text(json.dumps(complete,indent=2)+'\n');temp.replace(returned)
