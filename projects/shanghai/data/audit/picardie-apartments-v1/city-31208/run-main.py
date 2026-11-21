"""Run the control and independent phone and desktop directory sessions sequentially."""
import datetime,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
from process_family import chrome_descendants, still_alive
q=Path('/tmp/picardie208/final31208')
audit=Path('/workspace/e-resource/projects/shanghai/data/audit/picardie-apartments-v1')
signed=Path('/tmp/shanghai-yongjia-porch/scenes')
root_choice=q/'evidence-root.txt'
preferred=Path('/dev/shm/picardie208-main-31208')
if root_choice.exists():
 root=Path(root_choice.read_text().strip())
else:
 root=preferred if shutil.disk_usage('/dev/shm').free>=18*1024**2 else q/'main-evidence'
 root_choice.write_text(str(root)+'\n')
root.mkdir(exist_ok=True)
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
def remaining(tmp):
 alive=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:args=(p/'cmdline').read_bytes().split(bytes([0]));state=(p/'stat').read_text().rsplit(')',1)[1].split()[0]
  except OSError:continue
  if state!='Z'and b'chrom'in args[0]and any(os.fsencode(tmp)in arg for arg in args):alive.append(int(p.name))
 return alive
predecessor=Path('/tmp/haig207/207-city/207-map-slot-released.json')
released=json.loads(predecessor.read_bytes())
assert released['order']==207 and released['passed'] and released['final_closed_at']
assert released['after_real_screenshot_review'] and not released['remaining_chromium']
assert released['ports']==[31206,31207] and set(released['receipts'])=={'control','phone','desktop','return','placement','distant'}
for previous in released['receipts'].values():
 proof=Path(previous['closed'])
 assert previous['exit']==0 and hashlib.sha256(proof.read_bytes()).hexdigest()==previous['sha256']

actual=json.loads((q/'bound.json').read_bytes())
assert actual['passed'] and actual['pairs']['207']['count']==244 and actual['pairs']['208']['count']==245
results=[]
for name,num,flags,file in [('before', 207, ['--control'], 'control-browser.json'), ('phone', 208, ['--phone-only'], 'phone-browser.json'), ('phone-zoom', 208, ['--phone-zoom'], 'phone-browser.json'), ('desktop', 208, ['--desktop-card'], 'main-browser.json'), ('street', 208, ['--street'], 'main-browser.json'), ('paired', 208, ['--paired'], 'main-browser.json'), ('architecture', 208, ['--architecture'], 'main-browser.json'), ('terraces', 208, ['--terraces'], 'main-browser.json'), ('roof', 208, ['--roof'], 'main-browser.json'), ('distant', 208, ['--distant'], 'main-browser.json')]:
 out=root/name/'evidence'
 # Chromium creates its user profile in TMPDIR. Keep each profile on the filesystem
 # with more available space, separately from the small evidence location.
 profile_roots=[Path('/run/codex-docker/user'),Path('/dev/shm'),Path('/tmp')]
 previous_tmp_file=q/(name+'-profile-path.txt')
 tmp=max(profile_roots,key=lambda folder:shutil.disk_usage(folder).free)/('p8-'+name)
 out.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True)
 previous_tmp_file.write_text(str(tmp)+'\n')
 if (out/file).exists()and json.loads((out/file).read_bytes()).get('completed'):
  prior=json.loads((q/(name+'-closed.json')).read_bytes());assert prior['exit_code']==0 and not remaining(tmp);results.append(prior)
  if name=='before':subprocess.run(['python','-B',q/'offer-272-window.py'],check=True)
  if name=='phone':subprocess.run(['python','-B',q/'offer-272-viewer.py'],check=True)
  continue
 stage=q/'208'
 env={**os.environ,'TMPDIR':str(tmp),'QA_OUTPUT_DIR':str(out),'SHANGHAI_PROJECT_ROOT':str(stage),'MODEL_BASE_URL':f'http://127.0.0.1:{31000+num}/'}
 if name=='before':
  s=json.loads((signed/'207-comparison.json').read_bytes());binding=actual['pairs']['207'];assert s['passed'] and s['production_receipt_sha256']==binding['signature'] and s['catalog_sha256']==binding['catalog']
  env.update(QA_CONTROL_CATALOG=str(q/'207/data/candidate-city-integrations.json'),QA_CONTROL_CATALOG_SHA256=binding['catalog'],QA_CONTROL_CITY_COUNT=str(binding['count']))
 begin=now()
 with(q/(name+'.log')).open('ab',buffering=0)as log:
  process=subprocess.Popen(['node',q/'check-picardie-map.cjs',audit/'map-case.json',*flags],stdout=log,stderr=log,env=env,start_new_session=True)
  children={}
  while process.poll() is None:
   children.update(chrome_descendants(process.pid))
   time.sleep(.4)
  rc=process.returncode
 for i in range(15):
  if not remaining(tmp):break
  time.sleep(1)
 outcome={'name':name,'base':env['MODEL_BASE_URL'],'started_utc':begin,'finished_utc':now(),'pid':process.pid,'observed_chromium_pids_and_starttime':children,'exit_code':rc,'remaining_chromium':remaining(tmp),'report':str(out/file)}
 for pid,birth in children.items():
  try:
   fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
   if int(fields[19])==birth and fields[0] not in ('Z','X') and pid not in outcome['remaining_chromium']:outcome['remaining_chromium'].append(pid)
  except FileNotFoundError:pass
 outcome['browser_report_sha256']=__import__('hashlib').sha256((out/file).read_bytes()).hexdigest() if (out/file).is_file()else None
 (q/(name+'-closed.json')).write_text(json.dumps(outcome,indent=2)+'\n');results.append(outcome);assert rc==0 and children and not outcome['remaining_chromium'] and json.loads((out/file).read_bytes())['completed']
 if name=='before':subprocess.run(['python','-B',q/'offer-272-window.py'],check=True)
 if name=='phone':subprocess.run(['python','-B',q/'offer-272-viewer.py'],check=True)
(q/'all-main-outcomes.json').write_text(json.dumps(results,indent=2)+'\n')

subprocess.run(['python','-B',q/'physical-beacon.py'],check=True)

subprocess.run(['python','-B',q/'check-final-standalone.py'],check=True)
