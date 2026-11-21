"""Enter guest CPU jobs only after the corresponding observed browser sessions closed."""
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
w=Path(__file__).parent
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open("rb")as f:return hashlib.file_digest(f,"sha256").hexdigest()
def save(path,r):
    temp=path.with_suffix(".pending");temp.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n");temp.replace(path)
def now():return datetime.now(timezone.utc).isoformat()
def alive(pid):
    try:state=Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[-1].split()
    except FileNotFoundError:return False
    return state[0] not in ("Z","X")
def session_children(pid):
    children=[]
    for f in Path("/proc").glob("[0-9]*/stat"):
        try:r=f.read_text().rsplit(")",1)[1].split()
        except FileNotFoundError:continue
        if r[0] not in ("Z","X") and int(r[3])==pid:children.append(int(f.parent.name))
    return children
which=sys.argv[1]
if which=="338":
    a=Path("/tmp/park-fuxing338");session=Path("/tmp/shanghai-main-217/final-map-31217/touch/process.json")
    old=a/"217-touch-cpu-closed.json";record=read(old);physical=read(session)
    assert physical["exit_code"]==0 and physical["node_closed"] and not physical["remaining_children"] and not physical["remaining_chromium"]
    assert record["host_receipt_sha256"]==sha(session) and not record["remaining"]
    handback=w/"347-model-real-handoff.json";lower=read(handback)
    assert sha(Path(lower["actual_return"]))==lower["actual_sha256"] and not read(Path(lower["actual_return"]))["remaining"]
    if record.get("passed"):sys.exit(0)
    assert record.get("deferred") is True and record.get("started") is False
    prev=read(Path("/tmp/kemi334/217-offline-closed.json"));assert prev["passed"] and prev["exit_code"]==0 and not prev["remaining"]
    author=read(Path("/tmp/meilan337/author-package-ready.json"));assert author["passed"] and sha(Path(author["review"]))==author["source_sha256"] and sha(Path(author["dispatch"]))==author["dispatch_sha256"]
    target=a/"218-export-closed.json"
    if target.exists():
        rr=read(target);assert rr["previous_return_sha256"]==sha(handback) and not rr["remaining"];sys.exit(0)
    pkg=a/"design/pack-and-check.sh";lg=a/"218-export.log"
    with lg.open("xb") as log:
        start=now();task=subprocess.Popen(["bash",pkg],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);status=task.wait()
    rem=session_children(task.pid);assert not rem
    artifacts={k:sha(a/"pilot"/k) for k in ("surface-checks.json","geometry-input.json") if (a/"pilot"/k).is_file()}
    if status==0:assert len(artifacts)==2 and all(row["passed"]for row in read(a/"pilot/surface-checks.json")["results"].values())
    save(target,dict(order=338,host=218,host_receipt_sha256=sha(session),previous_217_deferred_sha256=sha(old),previous_return_sha256=sha(handback),program_sha256=sha(pkg),pid=task.pid,started=start,ended=now(),remaining=rem,passed=status==0,exit_code=status,log=str(lg),log_sha256=sha(lg),artifacts=artifacts))
elif which=="352":
    p=Path("/tmp/hujiang352-research/run-packed.py");assert sha(p)=="db9dcfb4fdfd45233f48ee803d396581166d1d64ae1cc7be7f4b8c6f9b12dc43"
    evidence=w/"three-scene-outcomes.json";rows=read(evidence)
    assert [r["tag"] for r in rows]==["before","phone","desktop"]
    for row in rows:
        assert row["node_closed"] and row["cdp_closed"] and row["exit_code"]==0 and not row["remaining_chromium"]
        assert not alive(row["node_pid"]) and row["chromium_pids"]
        assert not any(alive(pid)for pid in row["chromium_pids"])
        assert sha(Path(row["report"]))==row["report_sha256"]
    ticket=w/"352-city-closed.json"
    if not ticket.exists():save(ticket,dict(order=218,all_children_exited=True,remaining_children=[],sessions=str(evidence),sessions_sha256=sha(evidence),closed=now()))
    assert read(ticket)["sessions_sha256"]==sha(evidence)
    rr=p.parent/"packed-exit.json"
    if not rr.exists():
        child=subprocess.Popen([sys.executable,"-B",p,ticket],start_new_session=True)
        status=child.wait();assert not session_children(child.pid)
        assert read(rr)["exit_code"]==status
    r=read(rr);assert r["order"]==352 and r["prior_sha256"]==sha(ticket) and r["all_children_exited"] and not r["remaining_children"]
    save(w/"352-cpu-return.json",dict(program_sha256=sha(p),actual_return=str(rr),sha256=sha(rr),exit_code=r["exit_code"],remaining=[]))
else:raise ValueError(which)
