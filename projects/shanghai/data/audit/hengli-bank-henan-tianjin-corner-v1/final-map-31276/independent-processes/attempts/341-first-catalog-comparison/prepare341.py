from pathlib import Path
import json,hashlib,shutil,sys,subprocess
P=Path('/workspace/e-resource/projects/shanghai');D=Path('/workspace/shanghai-publisher-preservation/city-276');H=Path('/tmp/shanghai-main-276');W=Path('/tmp/fuxing341');T=W/'mapping/handoff';G=Path('/dev/net/i276');prior=D.parent/'city-275'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
def put(p,s):
 b=s.encode() if isinstance(s,str) else s;p.parent.mkdir(parents=True,exist_ok=True)
 if p.is_file() and p.read_bytes()==b:return
 tmp=p.with_name(p.name+'.new');tmp.write_bytes(b);tmp.replace(p)
def change(text,old,new):
 assert text.count(old)==1,(old,text.count(old));return text.replace(old,new)
def dump(q):return json.dumps(q,ensure_ascii=False,indent=2)+'\n'
code=(T/'six-view-download.cjs').read_text()
code=change(code,"const browser = await chromium.launch", "const device=process.env.SHANGHAI_341_DEVICE;assert(['desktop','mobile'].includes(device));\n  const browser = await chromium.launch")
code=change(code,"args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']","args: ['--no-sandbox','--no-zygote','--single-process','--in-process-gpu','--disable-dev-shm-usage','--num-raster-threads=1','--js-flags=--max-old-space-size=160']")
code=change(code,"for (const mobile of [false, true])","for (const mobile of [device==='mobile'])")
code=change(code,"const saved = path.join(process.env.TMPDIR, 'observed-' + item.file);","const saved = path.join(output, 'saved', 'observed-' + item.file);fs.mkdirSync(path.dirname(saved),{recursive:true});")
code=change(code,"saved_as:path.basename(saved), saveAsVerified:true","saved_as:path.basename(saved),saved:path.relative(output,saved), saveAsVerified:true").replace("            fs.rmSync(saved,{force:true});","")
code=change(code,"await browser.close();","await browser.close();report.device=device;report.closed=!browser.isConnected();report.finished=new Date().toISOString();")
code=change(code,"path.join(output, 'viewer.json')","path.join(output, device+'-viewer.json')")
phase=(T/'run-phase.py').read_text().replace("h/'admit-window.py'","h/'admit-window-live.py'").replace("h/'six-view-download.cjs'","h/'six-view-download-live.cjs'")
phase=change(phase,"attempt=h/(k+'-'+start.strftime('%Y%m%dT%H%M%S%f'));attempt.mkdir()","attempt=Path('/dev/net/i276/attempts')/(k+'-'+start.strftime('%Y%m%dT%H%M%S%f'));attempt.mkdir(parents=True)")
phase=phase.replace("Path('/run/codex-docker/user'),Path('/dev/shm')","Path('/dev/net'),Path('/dev/shm')")
phase=phase.replace('/tmp/country-tools/node_modules/.bin/gltfpack','/workspace/.e-resource-recovery/toolchain/node_modules/.bin/gltfpack').replace('/tmp/american-school127/oidn-single.py','/workspace/.e-resource-recovery/toolchain/one-thread/oidn-single.py')
phase=change(phase,"cmd=['node','-r',p/'data/audit/brunner-mond-v1/viewer-timeout.cjs',h/'six-view-download-live.cjs',id,attempt]","cmd=[sys.executable,'-Bu',h/'run-341-devices.py',id,attempt]")
phase=change(phase,"'node':proc.pid,'chromium_pids':chromes","'node':read(attempt/'desktop-node-exit.json')['node'],'node_pids':[read(attempt/(n+'-node-exit.json'))['node']for n in ['desktop','mobile']],'chromium_pids':chromes")
runner=(prior/'run-340-devices.py').read_text().replace('340','341').replace("six-view-download-recovered.cjs","six-view-download-live.cjs")
a=runner.index("j=read(data);");e=runner.index(" runs.append(j)",a)
runner=runner[:a]+"j=read(data);assert j['passed'] and j['device']==device and j['closed'] and len(j['views'])==3\n"+runner[e:]
runner=runner.replace("'rawSnapshotSHA256','productionSHA256',","").replace("'deviceRuns':desktop['deviceRuns']+mobile['deviceRuns']","'deviceRuns':[{'name':d['device'],'started':d['started'],'finished':d['finished'],'closed':d['closed']} for d in runs]")
ad=(T/'admit-window.py').read_text().replace("'run-phase.py'","'run-phase-live.py'").replace("h/'dispatch-contract.json'","h/'dispatch-live.json'")
ad=change(ad,"assert source==expected.resolve()","assert source.samefile(expected)")
ad=change(ad,"assert summary['screenshots']","assert summary['screenshots']\n driver=source.parent/'actual-driver.cjs';assert driver.is_file() and sha(driver)==row['driver_sha256']==summary['scriptSha256']\n assert sha(driver) in read(h/'dispatch-live.json')['actual_stage_drivers']")
ad=change(ad,"assert f.resolve().parent==source.parent.resolve() and f.stat()","assert shot['file']==Path(shot['file']).name and f.stat()")
for n,s in {'admit-window-live.py':ad,'run-phase-live.py':phase,'six-view-download-live.cjs':code,'run-341-devices.py':runner,'chromium-341-mesa':(prior/'chromium-340-mesa').read_text()}.items():
 if n.endswith('.py'):compile(s,n,'exec')
 for dest in [D,T]:
  put(dest/n,s)
  if n.startswith('chromium-'):(dest/n).chmod(0o755)
subprocess.run(['node','--check',T/'six-view-download-live.cjs'],check=True)
assets=P/'assets/models/candidates/huangpu-fuxing-fang-553-inscribed-balcony';(G/'issued').mkdir(exist_ok=True)
if not assets.exists():assets.symlink_to(G/'issued')
old=read(T/'dispatch-contract.json');mapping={Path(k):v for k,v in old['physical_inputs'].items()};assert all(f.is_file() and sha(f)==v for f,v in mapping.items());print('legacy',len(mapping))
driver=H/'final-map-31276/check-hengli-live.cjs'
extra=[T/'dispatch-contract.json',driver,H/'offer-341-live.py',prior/'guest-340-recovered.json',Path('/tmp/liuyazi340/mapping/handoff/dispatch-recovered.json'),Path('/tmp/liuyazi340/native-closed.json'),Path('/tmp/liuyazi340/viewer-closed.json'),Path('/tmp/liuyazi340/raw-340-confirmed.json'),Path('/tmp/shanghai-yongjia-porch/scenes/340-comparison.json'),Path('/workspace/.e-resource-recovery/grace/reboot245/276-341-physical-inputs.json'),Path('/workspace/.e-resource-recovery/toolchain/node_modules/.bin/gltfpack'),Path('/workspace/.e-resource-recovery/toolchain/one-thread/oidn-single.py'),*[T/n for n in ['admit-window-live.py','run-phase-live.py','six-view-download-live.cjs','run-341-devices.py','chromium-341-mesa']]]
mapping.update({f:sha(f)for f in extra})
current={**old,'admission_sha256':sha(T/'admit-window-live.py'),'physical_inputs':{str(f):v for f,v in mapping.items()},'actual_stage_drivers':[sha(driver)],'original_dispatch_sha256':sha(T/'dispatch-contract.json'),'independent_devices':{'desktop_views':3,'mobile_views':3,'actual_retained_desktop_downloads':4,'page':'fuxing-fang-553-inscribed-balcony.html'}}
put(T/'dispatch-live.json',dump(current));put(D/'dispatch-341-live.json',dump(current))
guest={**read(H/'guest-341.json'),'dispatch_sha256':sha(T/'dispatch-live.json'),'admission_sha256':sha(T/'admit-window-live.py'),'actual_driver_sha256':sha(driver),'original_guest_sha256':sha(H/'guest-341.json')}
for dest in [D,H]:put(dest/'guest-341-live.json',dump(guest))
print(sha(T/'dispatch-live.json'),sha(H/'guest-341-live.json'),sha(T/'admit-window-live.py'))
