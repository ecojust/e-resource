from pathlib import Path
import sys,subprocess,os,json,hashlib,shutil,tempfile,fcntl,time,datetime
root=Path(__file__).parent
home=root/'evidence/179'
D=home/'separate';D.mkdir(exist_ok=True)
old=home/'after';initial=home/'initial-after-renderer-interruption'
if old.exists()and not initial.exists():
 record=json.loads((old/'after.json').read_bytes());assert not record['completed']
 old.rename(initial)
script=root/'check-179.cjs';s=script.read_text()
base=s.index('    if(current){\n      await selectByLabel(false)')
end=s.index('      await page.goto(asURL(\'landmarks.html\')',base)
rest=s[end:]
s=s[:base]+"""    const part=process.env.CITY_SECTION;
    report.section=part;
    const nearest=owners.reduce((a,b)=>Math.hypot(a.point[0]-contract.lng,a.point[1]-contract.lat)<Math.hypot(b.point[0]-contract.lng,b.point[1]-contract.lat)?a:b);
    const nearestName=review.frozen_macro+'/'+near.find(g=>g.owners.includes(nearest.id)).group;
    if(part==='desktop'||part==='phone'){
      const phone=part==='phone';
      await page.setViewportSize(phone?{width:390,height:844}:{width:960,height:700});
      await selectByLabel(phone);
      await wait(g=>window.__SHANGHAI_APP__.scene.getStreamingState().detail.active.some(t=>t.id===g),nearestName); await stable();
      await shot(phone?'map-mobile':'map-desktop','full');
    }
    if(part==='details'||part==='distant'){
"""+rest
a=s.index("    }else{await page.goto(asURL('index.html#landmark='+previous",s.index("if(part==='details'||part==='distant')"));b=s.index('    const panel=',a)
s=s[:a]+"    }\n    if(part==='details'){\n"+s[b:]
s=s.replace("    if(current){await jump({...front,elevation:0,zoom:15.5,pitch:30});",'''    }
    if(part==='distant'){await page.setViewportSize({width:514,height:430});await jump({...front,elevation:0,zoom:15.5,pitch:30});''')
s=s.replace("const img=await page.screenshot({path:path.join(output,file),timeout:200000});","const session=await page.context().newCDPSession(page);let img;try{img=Buffer.from((await session.send('Page.captureScreenshot',{format:'png',fromSurface:true})).data,'base64');}finally{await session.detach();}fs.writeFileSync(path.join(output,file),img);")
a=s.index("    const required=[catalogName");b=s.index("    report.pageResponses",a)
s=s[:a]+"""    const required=part==='viewer'?[]:[catalogName,'src/app.js','src/map-scene.js','src/building-beacons.js',...(part==='details'?near.map(g=>g.file):[]),...(part==='distant'?[far.file,paths.get('lod').filePath]:[paths.get('full').filePath])];
    for(const file of required)assert.ok(received.has(file),'No verified response to the actual page request for '+file+' '+(unread.get(file)||''));
"""+s[b:]
s=s.replace("if(current){\n      // Leave", "if(part==='viewer'){\n      // Leave")
s=s.replace("const output", "const output") # Preserve original capture types.
s=s.replace("viewport:{width:960,height:700},hasTouch:true","viewport:{width:440,height:380},hasTouch:true")
s=s.replace("if(part==='details'||part==='distant'){","if(part==='details'){")
s=s.replace("if(part==='distant'){await page.setViewportSize({width:514,height:430});await jump({...front,elevation:0,zoom:15.5,pitch:30});","if(part==='distant'){await page.goto(asURL('index.html#landmark='+id+'&mode=overview'),{waitUntil:'domcontentloaded'});await wait(()=>Boolean(window.__SHANGHAI_APP__?.scene?.map));const toggle=page.locator('#panel-toggle');if(await toggle.getAttribute('aria-expanded')==='true')await toggle.click();await jump({...front,elevation:0,zoom:15.65,pitch:18});")
new=root/'check-179-distant-direct.cjs';new.write_text(s)
subprocess.run(['node','--check',new],check=True)
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/zhu-mintang-residence-v1')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
evidence=lambda p:json.loads(p.read_bytes())
snapshot=root/'179-production.json';case=root/'case179.json'
def alive(pid):
 p=Path('/proc')/str(pid)/'stat'
 try:return p.read_text().rsplit(')',1)[1].split()[0] not in ('Z','X')
 except FileNotFoundError:return False
def children(pid):
 nodes={pid};cmds={}
 for q in Path('/proc').glob('[0-9]*/stat'):
  try:
   num=int(q.parent.name);field=q.read_text().rsplit(')',1)[1].split();cmds[num]=(int(field[1]),(q.parent/'comm').read_text().strip())
  except (OSError,ValueError,IndexError):pass
 for _ in range(5):nodes.update(x for x,(p,_)in cmds.items()if p in nodes)
 return {x for x in nodes if x in cmds and cmds[x][1] in ('chromium','headless_shell')}
with (root/'browser.lock').open('a') as lock,Path('/tmp/shanghai-standalone-viewer.lock').open('a') as g:
 fcntl.flock(lock,fcntl.LOCK_EX);fcntl.flock(g,fcntl.LOCK_EX)
 for part in (sys.argv[1:]or ['phone','desktop','details','distant','viewer']):
  dst=D/part;dst.mkdir(exist_ok=True)
  if (dst/'closed.json').is_file():
   c=evidence(dst/'closed.json');assert c['exit']==0 and c['report_sha256']==sha(dst/'after.json');continue
  assert not (dst/'after.json').exists(),f'Retain failed {part} evidence in a new folder before retry'
  with tempfile.TemporaryDirectory(prefix=f'map179-{part}-')as tmp,(dst/'run.log').open('w')as output:
   proc=subprocess.Popen(['node',new,case,'after','http://127.0.0.1:31179/',snapshot,dst,home/'before/before.json'],env={**os.environ,'MODEL_AUDIT_DIR':str(audit),'NODE_PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules','TMPDIR':tmp,'CITY_SECTION':part},stdout=output,stderr=subprocess.STDOUT)
   seen=set()
   while proc.poll() is None:seen.update(children(proc.pid));time.sleep(.8)
   until=time.monotonic()+5
   while any(map(alive,seen))and time.monotonic()<until:time.sleep(.25)
   remains=[n for n in seen if alive(n)]
   report=dst/'after.json';c=dict(exit=proc.returncode,node=proc.pid,node_closed=not alive(proc.pid),chromium_pids=sorted(seen),remaining=remains,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),report_sha256=sha(report),driver_sha256=sha(new))
   (dst/'closed.json').write_text(json.dumps(c,indent=2)+'\n');print(part,c,flush=True)
   assert not remains and seen and c['node_closed'] and c['exit']==0
