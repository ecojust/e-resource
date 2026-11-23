"""Admit native or standalone work after the corresponding city 271 process and its children have closed."""
from datetime import datetime, timezone
from pathlib import Path
import argparse,ctypes,fcntl,os,shutil,subprocess,sys,time
import psutil
from receipts_recovered import HERE,WORK,PRIOR,FAMILY,completed_viewer,digest,native,prereqs,read,real_city_exit,write

def utc():return datetime.now(timezone.utc).isoformat()
def descendants(pid):
    try:return psutil.Process(pid).children(recursive=True)
    except psutil.Error:return []
def alive(pid,birth):
    try:
        p=psutil.Process(pid)
        return p.create_time()==birth and p.status() not in (psutil.STATUS_ZOMBIE,psutil.STATUS_DEAD)
    except psutil.Error:return False

def run_until_closed(kind,log):
    begin=utc();observed={}
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0)!=0:
        raise OSError(ctypes.get_errno(),'Unable to observe orphaned descendants')
    adopted=[]
    with log.open('xb')as out:
        command=[sys.executable,'-Bu',HERE/'run-phase-recovered.py',kind]
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT)
        observer=psutil.Process(child.pid);birth=observer.create_time()
        while child.poll() is None:
            for p in descendants(child.pid):
                try:observed[p.pid]=(p.create_time(),p.name())
                except psutil.Error:pass
            time.sleep(.03)
    exitcode=child.wait()
    # When an intermediate wrapper ends before a detached renderer, Linux
    # reparents it to this subreaper. ECHILD proves all such children have exited.
    while True:
        try:identifier,status=os.waitpid(-1,os.WNOHANG)
        except ChildProcessError:break
        if identifier:
            adopted.append({'pid':identifier,'exit_code':os.waitstatus_to_exitcode(status)})
        else:time.sleep(.05)
    while any(alive(p,start)for p,(start,_)in observed.items()):
        time.sleep(.2)
    receipt=dict(pid=child.pid,pid_birth=birth,started_at=begin,finished=utc(),exit_code=exitcode,
                 observed_descendants={p:{'birth':start,'name':name}for p,(start,name)in observed.items()},
                 adopted_children_reaped=adopted,no_waitable_children=True,wrapper_closed=not alive(child.pid,birth),remaining_children=[],remaining_chromium=[],remaining_blender=[])
    assert receipt['wrapper_closed']
    return receipt

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('kind',choices=('native','viewer'));parser.add_argument('source',type=Path)
args=parser.parse_args();kind=args.kind
source=args.source.absolute();host=real_city_exit(kind,source)
previous=[PRIOR/'native-closed.json',PRIOR/'raw-335-confirmed.json']
if kind=='viewer':
    previous += [PRIOR/'viewer-closed.json',WORK/'native-closed.json',WORK/'raw-336-confirmed.json',FAMILY/'scenes/336-comparison.json']

def defer(reason,launch=None):
    path=WORK/f'271-{kind}-deferred.json'
    payload=dict(order=336,host=271,stage=kind,kind=kind,authorized=False,deferred=True,host_receipt_sha256=digest(source),host_report_sha256=host['report_sha256'],
                 source=str(source),source_sha256=digest(source),previous_session=str(source),
                 previous_report_sha256=host['report_sha256'],reason=reason,attempted=launch is not None,
                 started=launch is not None,completed=False,checked_at=utc())
    if launch:payload.update(launch)
    if path.is_file():
        archive=HERE/(kind+'-previous-defer-'+digest(path)+'.json')
        if not archive.exists():shutil.copy2(path,archive)
        assert digest(archive)==digest(path)
        path.unlink()
    write(path,payload)

with (HERE/(kind+'.lock')).open('a')as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    end=WORK/(kind+'-closed.json')
    verify=native if kind=='native' else completed_viewer
    if end.exists():
        result=verify(end,336)
        assert result['host_receipt_sha256']==digest(source)
    elif not (HERE/'dispatch-recovered.json').exists():
        defer('The accepted inputs have not yet been bound.')
    else:
        missing=[str(p) for p in previous if not p.is_file()]
        if missing:
            defer('Waiting for the actual preceding records: '+', '.join(missing))
        else:
            try:
                grant=prereqs(kind,source)
            except (AssertionError,OSError,KeyError,TypeError,ValueError) as error:
                defer('Predecessor material did not pass verification: '+repr(error));sys.exit(0)
            grant_path=HERE/(kind+'-window.json')
            if grant_path.is_file() and read(grant_path)!=grant:
                old=HERE/(kind+'-prior-window-'+digest(grant_path)+'.json');write(old,read(grant_path));grant_path.unlink()
            write(grant_path,grant)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            log=HERE/(kind+'-launch-'+stamp+'.log');proc=run_until_closed(kind,log)
            closed=HERE/(kind+'-launch-'+stamp+'-closed.json');write(closed,proc)
            candidate=HERE/(kind+'-completed-'+grant['sha256']+'.json')
            if proc['exit_code']:
                defer('The admitted process exited before completing the requested verification.',dict(launch_log=str(log),launch_log_sha256=digest(log),launch_process=str(closed),launch_process_sha256=digest(closed),child_exit=proc['exit_code'],remaining_children=proc['remaining_children'],wrapper_closed=proc['wrapper_closed']))
            else:
                result=verify(candidate,336);assert result['host_receipt_sha256']==digest(source) and result['host_report_sha256']==host['report_sha256']
                result.update(launch_process=str(closed),launch_process_sha256=digest(closed),launch_log=str(log),launch_log_sha256=digest(log))
                write(end,result)
