"""Inspect the actual 277 release, then run 278 and leave the photographs for the reviewer."""
from pathlib import Path
import sys,json,subprocess,hashlib,fcntl
w=Path(__file__).parent;m=Path('/tmp/shanghai-main-277/277-map-slot-released.json')
def sha(f):
 with Path(f).open('rb')as fp:return hashlib.file_digest(fp,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def run(name,*args):subprocess.run([sys.executable,'-Bu',w/name,*args],check=True)
with (w/'admission.lock').open('a')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=load(m);assert p['order']==277 and p['passed'] and p['exit_code']==0 and p['remaining_chromium']==[]
 assert p['views_reviewed'] and p['all_captures_visually_reviewed'] and p['finished'] and p['manual_sha256']
 assert len(p['actual_saved_downloads'])==4
 source=Path('/tmp/shanghai-main-277/formal-31277')
 packet=load(source/'isolated-inputs.json')
 phases=packet['stage_order']
 assert p['reports']==p['real_browser_process_exits'] and [r['phase'] for r in p['reports']]==phases
 assert len(p['screenshots'])==len(phases) and sha(p['evidence'])==p['report_sha256']
 images={}
 for row in p['reports']:
  folder=source/'isolated-evidence'/row['phase'];physical_file=folder/'closed.json';q=load(physical_file)
  actual=load(q['report'])
  assert sha(physical_file)==row['closed_sha256'] and sha(q['report'])==q['report_sha256']==row['report_sha256']
  assert q['exit_code']==0 and q['cdp_closed'] and not q['remaining_chromium'] and q['observed_chromium_pid_and_starttime']==row['chromium']
  assert q['node_pid']==row['node'] and actual['completed'] and actual['phase']==row['phase']
  assert not actual['errors'] and not actual['failed'] and not actual['warnings']
  for image in actual['screenshots']:
   assert sha(folder/image['file'])==image['sha256'];images[image['file']]=image['sha256']
 assert images=={i['file']:i['sha256'] for i in p['screenshots']}
 standalone=source/'standalone-31277'
 viewer=load(standalone/'viewer.json')
 physical=load(source/'standalone-closed.json')
 assert physical==p['standalone_process'] and physical['passed'] and physical['exit']==0 and physical['chromium_pids'] and physical['remaining_chromium']==[]
 assert sha(standalone/'viewer.json')==physical['report_sha256']==p['standalone_sha256']
 assert viewer['base']=='http://127.0.0.1:31277/' and viewer['passed'] and viewer['views']==p['standalone_screens'] and len(viewer['views'])==6
 assert all(sha(standalone/im['filename'])==im['sha256'] for im in viewer['views'])
 assert len(viewer['downloads'])==4 and {v['sha256'] for v in viewer['downloads'].values()}=={v['sha256'] for v in p['actual_saved_downloads'].values()}
 helper=Path('/workspace/.e-resource-recovery/placement/host277-456/handoff-recovered.py');assert sha(helper)=='3b5822e90c0e06d7bbe5e29a45254b06006f38e689eb2002651ee6b5975f63c5'
 subprocess.run([__import__('sys').executable,'-Bu',helper,'wait'],check=True)
 next_guest=Path('/workspace/.e-resource-recovery/grace/host-277-280-guest-return.py');assert sha(next_guest)=='a42a74ffcd258867d2814e2c8bf49488d08de33497e0319975a2bbf5f7655bb2'
 __import__('subprocess').run([__import__('sys').executable,'-Bu',next_guest,'wait','453'],check=True)
 entry700=Path('/workspace/.e-resource-recovery/root/changning-700-study/development-native/link-277.py')
 assert hashlib.sha256(entry700.read_bytes()).hexdigest()=='9357ae1e77692c8439ef452abf716f30afe019f42e7b25a05856c2c2eb0fdffd'
 while not (entry700.parent/'early-development-returned.json').is_file():
  __import__('time').sleep(3)
 subprocess.run([__import__('sys').executable,'-Bu',entry700,'verify',Path('/tmp/shanghai-main-277/277-map-slot-released.json'),Path('/tmp/yuyuan750-453/development-native/277-development-returned.json')],check=True)
 if not(w/'catalogs-ready.json').exists():subprocess.run(['bash',w/'prime.sh'],check=True)
 run('local-catalogs.py','verify')
 run('run-278-live.py',m)
 run('merge-278-live.py')
 if not(w/'viewer-31278/closed.json').is_file():run('viewer-live.py','--assigned-standalone-slot')
 run('archive-live.py','278');run('local-catalogs.py','verify')
 print('278 actual captures await visual review',flush=True)
