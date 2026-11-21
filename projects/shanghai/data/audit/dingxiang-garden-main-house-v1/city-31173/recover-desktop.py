from pathlib import Path
from tempfile import TemporaryDirectory
import json,os,hashlib,datetime,subprocess,shutil,fcntl,time
w=Path(__file__).parent;sec=w/'segments';old=w/'first-desktop-return-crash';out=w/'return-recovery';out.mkdir(exist_ok=True);old.mkdir(exist_ok=True)
case=Path('/workspace/e-resource/projects/shanghai/data/audit/dingxiang-garden-main-house-v1/map-case.json')
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if (sec/'desktop').exists():
 (sec/'desktop').rename(old/'desktop');(sec/'desktop-closed.json').rename(old/'desktop-closed.json');(w/'exit').rename(old/'exit');(sec/'desktop.log').rename(old/'desktop.log')
original=w/'check-map.cjs';s=original.read_text();index=s.index("      if(segment==='desktop'){");end=s.index("      if(segment==='placement'){",index)
helper=s[s.index('      const viaDirectory=',index):s.index("      result.keyboardSearch=[",index)]
s=s[:index]+"""      if(segment==='return'){
      await page.goto(base+'index.html#landmark=hongkou-east-daming-road-378&mode=overview',{waitUntil:'domcontentloaded'});
      await page.waitForFunction(id=>{const scene=window.__SHANGHAI_APP__?.scene;return scene && !scene.map.isMoving() && !scene.getLandmarkAssetState(id)?.visible && !scene.getCandidateIntegrationState().clips.some(c=>c.id===id);},ID);
      await closePanel();result.unloadedWhileAway=true;
"""+helper+"""      result.keyboardSearch=[await viaDirectory('丁香花园',ID)];
      await view('map-returned','full');save();
      }
"""+s[end:];program=w/'check-return.cjs';program.write_text(s)
prev=read(old/'desktop/main-browser.json');c0=read(old/'desktop-closed.json');assert not prev['completed']and 'Target crashed'in prev['failure']and prev['unloadedWhileAway']and len(prev['keyboardSearch'])==3 and len(prev['screenshots'])==3 and c0['exit']==1 and not c0['remaining_chromium']
with Path('/tmp/shanghai-standalone-viewer.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with TemporaryDirectory(prefix='lilac173-return-',dir='/dev/shm')as folder:
  env=dict(os.environ,NODE_PATH='/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules',TMPDIR=folder,SHANGHAI_PROJECT_ROOT=str(w/'city173'),QA_SEGMENT='return',QA_OUTPUT_DIR=str(out),QA_CDP_PORT='9873',MODEL_BASE_URL='http://127.0.0.1:31173/')
  with(out/'run.log').open('ab')as log:pr=subprocess.Popen(['node',program,case],env=env,stdout=log,stderr=log,start_new_session=True);rc=pr.wait()
  def left():
   ps=[]
   for f in Path('/proc').glob('[0-9]*/cmdline'):
    try:c=f.read_bytes()
    except OSError:continue
    if b'chromium' in c and folder.encode()in c:ps.append(int(f.parent.name))
   return ps
  for i in range(20):
   if not left():break
   time.sleep(.4)
  f=out/'main-browser.json';r=read(f);closure=dict(name='return',exit=rc,node_pid=pr.pid,remaining_chromium=left(),report=str(f),report_sha256=sha(f),started=begin,finished=datetime.datetime.now(datetime.timezone.utc).isoformat());write(out/'closed.json',closure)
  assert rc==0 and not closure['remaining_chromium'] and r['completed'] and len(r['screenshots'])==1
o=sec/'desktop';o.mkdir();d={k:v for k,v in r.items() if k not in ['segment','scriptSha256','views','screenshots','keyboardSearch','beaconInputs']};d.update(segment='desktop',scriptSha256=sha(original),started=prev['started'],views=prev['views']+r['views'],screenshots=prev['screenshots']+r['screenshots'],keyboardSearch=prev['keyboardSearch'],beaconInputs=prev['beaconInputs'],neighborSelection=prev['neighborSelection'],defaultTimeline=prev['defaultTimeline'],recovery=dict(original_sha256=sha(old/'desktop/main-browser.json'),original_exit=1,return_report_sha256=sha(f),return_program_sha256=sha(program),return_exit=0,reason='The initial desktop reached selection of the return landmark; its renderer exited before drawing the frame. An independently reopened public scene repeated the distant-to-return keyboard transition and captured the missing frame.'))
for img in d['screenshots']:
 path=(old/'desktop'/img['file']) if (old/'desktop'/img['file']).is_file()else out/img['file'];assert sha(path)==img['sha256'];os.link(path,o/img['file'])
write(o/'main-browser.json',d);write(sec/'desktop-closed.json',dict(closure,name='desktop',report=str(o/'main-browser.json'),report_sha256=sha(o/'main-browser.json'),recovery=d['recovery']))
subprocess.run([os.environ.get('PYTHON','python'),'-Bu',w/'physical-segments.py'],check=True)
