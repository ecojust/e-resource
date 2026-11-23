"""Drive actual Chromium through CDP's local pipe using one standard-library process."""
import argparse, base64, fcntl, hashlib, json, math, os, select, shutil, signal, socket, sys, tempfile, threading, time
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer

class HTTP(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def data(p):return json.loads(p.read_bytes())
def dump(p,v):
    tmp=p.with_suffix('.new');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def launch(log,profile,device,backend,binary):
    a,b=os.pipe();c,d=os.pipe()
    inp,out=[fcntl.fcntl(fd,fcntl.F_DUPFD_CLOEXEC,12) for fd in (a,d)]
    logfd=fcntl.fcntl(log.fileno(),fcntl.F_DUPFD_CLOEXEC,12)
    pid=os.fork()
    if not pid:
        os.dup2(inp,3);os.dup2(out,4)
        os.dup2(logfd,1);os.dup2(logfd,2)
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        args=[binary,'--remote-debugging-pipe','--no-sandbox','--single-process','--no-zygote','--in-process-gpu','--disable-dev-shm-usage',
              '--headless=new','--ozone-platform=headless','--use-gl=angle','--use-angle='+backend,'--enable-unsafe-swiftshader','--ignore-gpu-blocklist',
              '--disable-sync','--disable-features=MediaRouter,OptimizationHints,Translate,AutofillServerCommunication,BackForwardCache','--no-first-run',
              '--disable-background-networking','--disable-component-update','--disable-extensions','--disable-breakpad','--disable-gpu-watchdog',
              '--num-raster-threads=1','--disable-gpu-compositing','--disable-gpu-rasterization','--disable-gpu-shader-disk-cache','--disable-gpu-program-cache',
              '--enable-low-end-device-mode','--force-gpu-mem-available-mb=16','--disk-cache-size=524288','--js-flags=--optimize-for-size --max-old-space-size=40 --max-semi-space-size=1',
              '--user-data-dir='+str(profile),'--window-size=390,620','about:blank']
        env=dict(os.environ, TMPDIR=str(profile.parent), LIBGL_ALWAYS_SOFTWARE='1',LP_NUM_THREADS='1',GALLIVM_PERF='no_opt',LP_NATIVE_VECTOR_WIDTH='128',
                 OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MALLOC_ARENA_MAX='1')
        os.execve(binary,args,env)
    for fd in (a,d,inp,out,logfd):os.close(fd)
    return pid,Pipe(c,b)
class Pipe:
    def __init__(self,read,write):
        self.read=read;self.write=write;self.buf=b'';self.id=0;self.events=[];self.session=None
    def next(self,deadline):
        while b'\0' not in self.buf:
            available,_,_=select.select([self.read],[],[],max(0,deadline-time.monotonic()))
            if not available:raise TimeoutError('CDP timeout')
            part=os.read(self.read,65536)
            if not part:raise EOFError('Chromium closed its DevTools pipe')
            self.buf+=part
        msg,self.buf=self.buf.split(b'\0',1)
        return json.loads(msg)
    def call(self,method,params=None,tab=True,timeout=20):
        self.id+=1
        request=dict(id=self.id,method=method,params=params or {})
        if tab and self.session:request['sessionId']=self.session
        wire=json.dumps(request,separators=(',',':')).encode()+b'\0'
        while wire:wire=wire[os.write(self.write,wire):]
        deadline=time.monotonic()+timeout
        while True:
            msg=self.next(deadline)
            if msg.get('id')==self.id:
                if msg.get('error'):raise ValueError((method,msg['error']))
                return msg.get('result',{})
            if msg.get('method') in ['Browser.downloadWillBegin','Browser.downloadProgress','Runtime.exceptionThrown','Network.responseReceived']:
                self.events.append(msg)
    def js(self,code):
        v=self.call('Runtime.evaluate',dict(expression=code,returnByValue=True,awaitPromise=True))
        if 'exceptionDetails' in v:raise ValueError(v['exceptionDetails'])
        return v['result'].get('value')
    def until(self,code):
        deadline=time.monotonic()+25
        while time.monotonic()<deadline:
            v=self.js(code)
            if v:return v
            time.sleep(.08)
        raise TimeoutError((code,self.js("document.querySelector('#status')?.textContent")))
    def click(self,selector,mobile):
        code="""(()=>{const e=document.querySelector(SEL);e.scrollIntoView({block:'center',inline:'center'});let r=e.getBoundingClientRect();let x=(Math.max(0,r.left)+Math.min(innerWidth,r.right))/2,y=(Math.max(0,r.top)+Math.min(innerHeight,r.bottom))/2;return [x,y,e.contains(document.elementFromPoint(x,y))]})()"""
        x,y,visible=self.js(code.replace('SEL',json.dumps(selector)));assert visible,selector
        if mobile:
            self.call('Input.dispatchTouchEvent',dict(type='touchStart',touchPoints=[dict(x=x,y=y)]))
            self.call('Input.dispatchTouchEvent',dict(type='touchEnd',touchPoints=[]))
        else:
            for state in ['mousePressed','mouseReleased']:
                self.call('Input.dispatchMouseEvent',dict(type=state,x=x,y=y,button='left',clickCount=1))

def run(device,stage,backend,site,output,chromium,scratch):
    key='changning-xinhua-231-rong-garden-roof';slug='xinhua-231-rong-garden-roof'
    model=Path('assets/models/candidates')/key;src=Path('source/precise')/key/'source'
    page=slug+'.html'
    out=output/device/stage/time.strftime('%Y%m%d-%H%M%S',time.gmtime());out.mkdir(parents=True)
    saved=out/'saved';saved.mkdir()
    http=ThreadingHTTPServer(('127.0.0.1',0),partial(HTTP,directory=site))
    address=f'http://127.0.0.1:{http.server_port}/';mobile=device=='phone'
    width,height=(390,760) if mobile else (1024,690)
    manifest=data(site/model/'manifest.json');views=data(site/src/'cameras.json')
    roles={**manifest['assets'],**manifest['interchange']};roles['source']={'file':key+'-source.zip'}
    assert len(roles)==8
    report=dict(id=key,page=page,device=device,stage=stage,viewport=[width,height],backend=backend,started=time.time(),
                source_files={str(p):sha(site/p) for p in (Path(page),src/'viewer.js',src/'cameras.json',model/'manifest.json')},
                screenshots=[],downloads={},transitions=[],remaining=[],driver_sha256=sha(Path(__file__)))
    with tempfile.TemporaryDirectory(dir=scratch,prefix='xinhua-ui-') as tmp,(out/'chromium.log').open('wb') as log:
        pid,client=launch(log,Path(tmp)/'profile',device,backend,chromium);report['pid']=pid
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        passed=False
        try:
            client.call('Browser.getVersion',tab=False)
            t=next(t for t in client.call('Target.getTargets',tab=False)['targetInfos'] if t['type']=='page')
            client.session=client.call('Target.attachToTarget',dict(targetId=t['targetId'],flatten=True),tab=False)['sessionId']
            client.call('Page.enable');client.call('Runtime.enable');client.call('Network.enable')
            client.call('Emulation.setDeviceMetricsOverride',dict(width=width,height=height,deviceScaleFactor=.5,mobile=mobile))
            client.call('Emulation.setTouchEmulationEnabled',dict(enabled=mobile,maxTouchPoints=1 if mobile else 1))
            client.call('Browser.setDownloadBehavior',dict(behavior='allow',downloadPath=str(saved),eventsEnabled=True),tab=False)
            client.call('Page.navigate',dict(url=address+page))
            client.until("document.querySelector('#model-view')?.dataset.role==='full'")
            report['gl']=client.js("""(()=>{const c=document.querySelector('#model-view canvas'),g=c.getContext('webgl2');const ext=g.getExtension('WEBGL_debug_renderer_info');return {version:g.getParameter(g.VERSION),renderer:g.getParameter(ext?ext.UNMASKED_RENDERER_WEBGL:g.RENDERER),buffer:[g.drawingBufferWidth,g.drawingBufferHeight],userAgent:navigator.userAgent,touch:navigator.maxTouchPoints}})()""")
            assert report['gl']['version'].startswith('WebGL 2')
            render_frame="""new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))"""
            if stage in ('cameras','all'):
                client.js("""(async()=>{const T=await import('/vendor/three.module.js');const prev=T.PerspectiveCamera.prototype.updateMatrixWorld;T.PerspectiveCamera.prototype.updateMatrixWorld=function(...args){const r=prev.apply(this,args),e=this.matrixWorld.elements;window.__actualCamera={eye:this.position.toArray(),direction:[-e[8],-e[9],-e[10]],fov:this.fov,aspect:this.aspect};return r};return true})()""")
                for view in views:
                    name=view['name'];client.click('button[data-view='+json.dumps(name)+']',mobile)
                    client.js("document.querySelector('#model-view canvas').scrollIntoView({block:'center',inline:'nearest'})")
                    client.js(render_frame)
                    state=client.js("""(()=>{let r=document.querySelector('#model-view canvas').getBoundingClientRect();return {camera:window.__actualCamera,view:document.querySelector('#model-view').dataset.view,clip:{x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height,scale:1}}})()""")
                    assert state['view']==name and state['camera']
                    c=state['camera'];world=lambda v:(v[0],v[2],-v[1]);eye=world(view['eye']);target=world(view['target']);delta=[t-e for t,e in zip(target,eye)];length=math.hypot(*delta)
                    assert max(abs(a-b) for a,b in zip(eye,c['eye']))<1e-5 and max(abs(a/length-b) for a,b in zip(delta,c['direction']))<1e-5
                    expected=math.degrees(2*math.atan(math.tan(math.radians(view['fov'])/2)/min(1,c['aspect'])))
                    assert abs(c['fov']-expected)<1e-5
                    shot=out/(device+'-'+name+'.jpg')
                    capture=client.call('Page.captureScreenshot',dict(format='jpeg',quality=85,clip=state['clip'],fromSurface=True))
                    shot.write_bytes(base64.b64decode(capture['data']))
                    report['screenshots'].append(dict(view=name,actual=c,file=shot.name,bytes=shot.stat().st_size,sha256=sha(shot)))
                    dump(out/'running.json',report)
                assert len({s['sha256'] for s in report['screenshots']})==len(views)
            if stage in ('lod','all'):
                for option in ['lod','full','auto']:
                    client.js("""(()=>{const el=document.querySelector('#detail');el.value=VAL;el.dispatchEvent(new Event('change',{bubbles:true}));return el.value})()""".replace('VAL',json.dumps(option)))
                    expected='lod' if option=='lod' else 'full'
                    client.until("document.querySelector('#model-view').dataset.role==="+json.dumps(expected))
                    report['transitions'].append([option,expected])
                if not mobile:
                    pos=client.js("(()=>{let r=document.querySelector('#model-view canvas').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()")
                    client.call('Input.dispatchMouseEvent',dict(type='mouseWheel',deltaX=0,deltaY=2200,**pos))
                    client.until("document.querySelector('#model-view').dataset.role==='lod'")
                    client.click('button[data-view='+json.dumps(views[1]['name'])+']',False)
                    client.until("document.querySelector('#model-view').dataset.role==='full'")
                    report['transitions'] += [['auto-wheel','lod'],['auto-camera','full']]
                dump(out/'running.json',report)
            if stage in ('files','all'):
                for role,item in roles.items():
                    file=item['file'];local=site/model/file
                    selector='#download-source' if role=='source' else '#downloads [data-role='+json.dumps(role)+']'
                    client.click(selector,mobile)
                    dest=saved/file;deadline=time.monotonic()+15
                    while time.monotonic()<deadline:
                        client.call('Browser.getVersion',tab=False)
                        receipts=[m['params'] for m in client.events if m['method']=='Browser.downloadWillBegin' and m['params']['suggestedFilename']==file]
                        complete=bool(receipts and any(m['method']=='Browser.downloadProgress' and m['params'].get('guid')==receipts[-1]['guid'] and m['params']['state']=='completed' for m in client.events))
                        if complete and dest.is_file() and dest.stat().st_size==local.stat().st_size:break
                        time.sleep(.06)
                    assert complete and dest.is_file() and sha(dest)==sha(local),file
                    if role!='source':assert item['sha256']==sha(dest) and item['bytes']==dest.stat().st_size
                    report['downloads'][role]=dict(file=file,bytes=dest.stat().st_size,sha256=sha(dest),completed=True)
                    dump(out/'running.json',report)
                assert len(report['downloads'])==8
            report['model_responses']=[{'file':m['params']['response']['url'].split('/')[-1],'status':m['params']['response']['status']} for m in client.events if m['method']=='Network.responseReceived' and m['params']['response']['url'].endswith('.glb')]
            errors=[m for m in client.events if m['method']=='Runtime.exceptionThrown'];assert not errors,errors
            passed=True
        finally:
            try:client.call('Browser.close',tab=False,timeout=3)
            except (OSError,ValueError,EOFError,TimeoutError):pass
            until=time.monotonic()+10
            while time.monotonic()<until:
                done,status=os.waitpid(pid,os.WNOHANG)
                if done:break
                time.sleep(.08)
            else:
                os.kill(pid,signal.SIGTERM);_,status=os.waitpid(pid,0)
            report['exit']=os.waitstatus_to_exitcode(status);report['passed']=passed and report['exit']==0
            report['finished']=time.time();dump(out/'report.json',report)
            http.shutdown();http.server_close();thread.join()
            os.close(client.read);os.close(client.write)
        assert report['passed']
    print(out,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('device',choices=['desktop','phone'])
    parser.add_argument('stage',choices=['cameras','lod','files','all'])
    parser.add_argument('--backend',default='swiftshader')
    parser.add_argument('--site',type=Path,required=True,help='Path to a complete published projects/shanghai tree')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--chromium',default=shutil.which('chromium') or shutil.which('chromium-browser'))
    parser.add_argument('--scratch',type=Path,default=None)
    a=parser.parse_args()
    if not a.chromium:parser.error('Chromium binary required')
    run(a.device,a.stage,a.backend,a.site.resolve(),a.output.resolve(),a.chromium,a.scratch)

