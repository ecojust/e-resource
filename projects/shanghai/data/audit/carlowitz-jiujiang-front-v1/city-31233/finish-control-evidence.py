from pathlib import Path
from hashlib import sha256
import subprocess,os,sys,json
w=Path(__file__).resolve().parent;orig=w/'isolated-evidence/control';a=w/'fifth-control-composited/control';d=w/'control-device-followup';d.mkdir(exist_ok=True);a.parent.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_bytes());h=lambda p:sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
if not a.exists():orig.rename(a)
orig.mkdir(exist_ok=True);report=a/'control-browser.json';source=read(report);close=a/'failed-exit.json';physical=read(close)
assert not source['completed'] and 'check-carlowitz.cjs:385:' in source['failure'] and len(source['views'])==1 and len(source['files'])==12 and len(source['servedRuntime'])==9
assert source['errors']==source['warnings']==source['failed']==[] and physical['report_sha256']==h(report) and physical['exit_code']==1 and not physical['remaining_chromium'] and physical['cdp_closed']
view=source['views'][0];frame,=source['screenshots'];assert view['glError']==0 and not view['contextLost'] and len(view['neighbors'])==9 and frame==source['compositorFrame'] and h(a/frame['file'])==frame['sha256'] and frame['cameraAtRead']['visibleGroup']
assert view['clip'] is None and source['realDirectoryEntry']['pointer']['trusted'] and all(x['loadedByScene']for x in source['files'][-2:])
device_file=d/'input-device.json'
if not device_file.exists():
 with (d/'node.log').open('a')as f:
  res=subprocess.run(['node',w/'read-control-device.cjs'],env=dict(os.environ,QA_CDP_PORT='19533',TMPDIR=str(w/'browser-work')),stdout=f,stderr=subprocess.STDOUT)
 put(d/'node-exit.json',dict(exit_code=res.returncode));assert res.returncode==0
item=read(device_file);assert item['passed'] and item['exit']=={'code':0,'signal':None} and item['source_map_session_sha256']==h(report) and read(d/'node-exit.json')['exit_code']==0
for pid in (item['chromium_pid'],item['node_pid']): assert not Path(f'/proc/{pid}/stat').is_file()
shared=dict(map=dict(source=str(report),report_sha256=h(report),close=str(close),close_sha256=h(close),exit_code=1,sha256_of_presented_frame=frame['sha256']),device=dict(source=str(device_file),report_sha256=h(device_file),program_sha256=h(w/'read-control-device.cjs'),node_exit_sha256=h(d/'node-exit.json'),exit_code=0))
combined=dict(source);combined.pop('failure');combined.pop('failureState',None);combined.update(completed=True,single_session_completed=False,observed_in_separate_sessions=shared,inputDevice=item['inputDevice'],finished=item['finished'])
put(orig/'control-browser.json',combined)
if not (orig/frame['file']).exists():os.link(a/frame['file'],orig/frame['file'])
put(orig/'closed.json',dict(order=233,phase='control',aggregate=True,exit_code=0,started=physical['started'],finished=item['finished'],node_pid=item['node_pid'],observed_chromium_pid_and_starttime={str(item['chromium_pid']):item['birth']},remaining_chromium={},cdp_closed=True,source_code_sha256=source['scriptSha256'],device_program_sha256=h(w/'read-control-device.cjs'),source_driver_note='Source SHA for the map session. The separate device session has its own program SHA and process IDs.',predecessor=physical['predecessor'],report=str(orig/'control-browser.json'),report_sha256=h(orig/'control-browser.json'),observed_in_separate_sessions=shared))
print('verified 12 served files, 9 source modules, 9 neighbors, composited frame, and separate device profile',h(orig/'closed.json'))
