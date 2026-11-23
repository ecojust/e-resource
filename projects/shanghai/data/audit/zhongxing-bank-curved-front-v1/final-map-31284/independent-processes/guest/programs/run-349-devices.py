"""Run each device in its own Node and Chromium and retain both original reports."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
h=Path(__file__).resolve().parent
w=h.parent
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT','/workspace/e-resource/projects/shanghai'))
ident,output=sys.argv[1:];out=Path(output)
read=lambda p:json.loads(p.read_bytes())
def sha(p):
 with p.open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def save(p,v):
 t=p.with_suffix(p.suffix+'.next');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');t.replace(p)
runs=[]
for device in ['desktop','mobile']:
 env={**os.environ,'SHANGHAI_349_DEVICE':device,'QA_OUTPUT_DIR':str(out),'QA_CDP_PORT':'29493' if device=='desktop' else '29494','CHROMIUM_PATH':str(h/'chromium-349-mesa'),
      'NODE_OPTIONS':'--unhandled-rejections=warn --max-old-space-size=96','DEBUG':'pw:browser'}
 start=time.time_ns();cmd=['node','-r',project/'data/audit/brunner-mond-v1/viewer-timeout.cjs',h/'six-view-live.cjs',ident,out]
 with (out/(device+'-node.log')).open('xb')as log:
  run=subprocess.Popen(cmd,stdout=log,stderr=log,env=env);exe=Path(os.readlink('/proc/'+str(run.pid)+'/exe')).name;assert exe=='node';run.wait()
 data=out/(device+'-viewer.json')
 state=dict(device=device,node=run.pid,node_executable=exe,started_ns=start,finished_ns=time.time_ns(),exit=run.returncode,report_sha256=sha(data)if data.is_file()else None)
 save(out/(device+'-node-exit.json'),state)
 if run.returncode:sys.exit(run.returncode if run.returncode>0 else 1)
 j=read(data);assert j['passed'] and j['device']==device and j['closed'] and len(j['views'])==3
 runs.append(j)
desktop,mobile=runs
for key in ['base','route','id','files','scriptSHA256','manifestSHA256']:
 assert desktop[key]==mobile[key],key
assert not desktop['pageErrors'] and not mobile['pageErrors']
assert set(desktop['downloads'])=={'raw','full','lod','native'}
for frame in [*desktop['views'],*mobile['views']]:assert sha(out/frame['filename'])==frame['sha256']
for entry in desktop['downloads'].values():assert sha(out/'saved'/entry['saved_as'])==entry['sha256']
combined={**desktop,'views':desktop['views']+mobile['views'],'deviceRuns':[{'name':d['device'],'started':d['started'],'finished':d['finished'],'closed':d['closed']} for d in runs],
          'chromium_launch_file_sha256':sha(h/'chromium-349-mesa'),'independent_device_reports':{v+'-viewer.json':sha(out/(v+'-viewer.json'))for v in ['desktop','mobile']}}
assert combined['deviceRuns'][0]['finished']<combined['deviceRuns'][1]['started']
save(out/'viewer.json',combined)
