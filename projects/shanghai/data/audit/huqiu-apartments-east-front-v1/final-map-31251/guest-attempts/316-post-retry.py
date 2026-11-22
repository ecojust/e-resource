"""Run the remaining checks on the original 316 build and retain its actual process record."""
from pathlib import Path
import os,datetime,sys,subprocess,fcntl,json,hashlib
HERE=Path('/tmp/kangding759-316/mapping/handoff')
sys.path.insert(0,str(HERE))
from receipts_recovered import ASSETS,AUDIT,WORK,digest,prereqs,read,write,native
attempt=HERE/'native-attempt-2026-11-22T144303.354250-0000'
kind='native'
grant=read(HERE/'native-window.json')
assert prereqs(kind,Path(grant['receipt']))==grant
source=Path('/workspace/e-resource/projects/shanghai/source/precise/jingan-zhu-douwen-residence-side-porch/source')
ID='jingan-zhu-douwen-residence-side-porch'
original=HERE/'run-recovered.py'
dispatch=read(HERE/'dispatch-recovered.json')
assert digest(original)==dispatch['programs_and_inputs'][str(original)]
manifest=Path(dispatch['accepted_manifest']);ref=read(manifest)['assets']
common=read(attempt/'process-exit.json');children=common['observed_processes']
assert common['exit']==common['exit_code']==0 and not common['remaining'] and common['wrapper_closed']
assert common['log_sha256']==digest(attempt/'run.log') and common['admitted_from']==grant['sha256'] and common['parent_snapshot_sha256']==grant['parent_snapshot_sha256']
assert 'No space left on device' in (HERE/'native-20261122T144303272060Z.log').read_text()
tmp=Path('/run/codex-docker/user/316-post-geometry');tmp.mkdir(exist_ok=True)
os.environ['TMPDIR']=str(tmp)
code=original.read_text();checks=code[code.index("    done=read(ASSETS/'manifest.json')"):code.index('    else:\n        seen=[pid',code.index("    done=read(ASSETS/'manifest.json')"))]
with (HERE/'native.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 if not (WORK/'native-closed.json').is_file():
  checks=checks.replace("HERE/'post-geometry.py'","Path('/workspace/shanghai-publisher-preservation/city-251/post-geometry-316-with-frozen-camera.py')")
  exec(compile('if True:\n'+checks,str(original),'exec'))
  result.update(post_geometry_retried=True,original_process_sha256=digest(attempt/'process-exit.json'),post_geometry_sha256=digest(WORK/'post-geometry.json'),post_geometry_finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
  write(WORK/'native-closed.json',result)
 native(WORK/'native-closed.json',316);print(digest(WORK/'native-closed.json'),flush=True)
