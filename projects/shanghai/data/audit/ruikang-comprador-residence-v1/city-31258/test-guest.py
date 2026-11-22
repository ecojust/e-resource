"""Check the three observed 323 outcome formats against both 258 windows, including corrupt receipts."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,os,subprocess,sys
import psutil
from guest_result import digest,verify
def save(path,obj):
 path.write_text(json.dumps(obj,sort_keys=True)+'\n')
 return path
with TemporaryDirectory(prefix='guest-323-fixture-') as directory:
 w=Path(directory)
 count=0
 for kind,phase in [('native','before'),('viewer','phone')]:
  report=save(w/'report.json',{'fixture':True,'phase':phase})
  host=save(w/'closed.json',dict(order=258,phase=phase,exit_code=0,node_closed=True,remaining=[],remaining_chromium=[],report=str(report),report_sha256=digest(report)))
  stamp=w/'guest.json'
  def check(value,expected=None):
   try:out=verify(kind,host,save(stamp,value))
   except (AssertionError,KeyError):
    if expected:raise
   else:assert out==expected and expected
  common=dict(order=323,kind=kind,host_report_sha256=digest(report),host_receipt_sha256=digest(host))
  deferred={**common,'host':258,'deferred':True,'source':str(host),'source_sha256':digest(host),'blender_started':False,'chromium_started':False,'browser_started':False,'started':False,'attempted':False,'missing':['signed-parent']}
  check(deferred,'deferred-before-launch')
  for key,bad in [('source_sha256','0'*64),('host_report_sha256','0'*64),('missing',[]),('browser_started',True)]:check({**deferred,key:bad})
  log=w/'process.log'
  with log.open('wb') as out:
   child=subprocess.Popen([sys.executable,'-c','import time,sys;time.sleep(.035);sys.exit(7)'],stdout=out)
   birth=psutil.Process(child.pid).create_time();code=child.wait()
  proc={**common,'pid':child.pid,'started':'2026-11-21T10:00:00Z','finished':'2026-11-21T10:01:00Z','exit':code,'observed_children':{str(child.pid):birth},'remaining':[],'wrapper_closed':True}
  process=save(w/'launch-process.json',proc)
  failed={**proc,'attempted':True,'started':True,'passed':False,'remaining_children':[],'launch_log':str(log),'launch_log_sha256':digest(log),'launch_process':str(process),'launch_process_sha256':digest(process)}
  check(failed,'deferred-after-physical-exit')
  for key,bad in [('exit',0),('attempted',False),('host_receipt_sha256','0'*64),('launch_log_sha256','0'*64)]:check({**failed,key:bad})
  live={str(os.getpid()):psutil.Process().create_time()};save(process,{**proc,'observed_children':live})
  check({**failed,'observed_children':live,'launch_process_sha256':digest(process)})
  success={**common,'passed':True,'exit':0,'remaining_blender':[],'remaining_oidn':[],'remaining_chromium':[]}
  check(success,'complete');check({**success,'host_receipt_sha256':'0'*64})
  count+=13
 print(count,'two-window outcome checks passed')
