from hashlib import sha256
from pathlib import Path
import json
def verify(audit,order,names):
 assert order==251
 root=audit/'final-map-31251'
 p=root/'guest-attempts';returns=root/'guest-returns'
 def sha(f):return sha256(f.read_bytes()).hexdigest()
 def read(f):return json.loads(f.read_bytes())
 rows=read(p/'checksums.json')
 assert all(sha(p/n)==sig for n,sig in rows.items())
 status=read(p/'316-original-process.json');result=read(returns/'316-native.json')
 assert result['exit']==status['exit']==0 and not result['remaining'] and not status['remaining'] and result['post_geometry_retried']
 assert result['group_count']==85 and result['original_process_sha256']==sha(p/'316-original-process.json')
 assert len(result['blender_pids'])==2 and status['log_sha256']==sha(p/'316-original-build.log')
 assert b'Reopened 85 editable meshes and 28212 triangles' in (p/'316-original-build.log').read_bytes()
 assert b'No space left on device' in (p/'316-post-disk.log').read_bytes() and b'AssertionError: camera-sightlines.json' in (p/'316-post-camera.log').read_bytes()
 assert b'returned non-zero exit status 1' in (p/'316-before-original-outer.log').read_bytes()
 assert result['post_geometry_sha256']==sha(returns/'316-post-geometry.json') and len(read(returns/'316-post-geometry.json')['proofs'])==6
 after=read(returns/'596-independent-returned.json')
 assert b'FileNotFoundError:' in (p/'596-missing-driver-before-entry.log').read_bytes() and b'current-standalone/formal-viewer.cjs' in (p/'596-missing-driver-before-entry.log').read_bytes()
 assert after['host_sha256']==sha(root/'current-standalone/closed.json') and after['exit_code']==0 and after['passed'] and after['all_children_exited'] and not after['remaining_children']
 assert (root/'current-standalone/formal-viewer.cjs').is_file() and sha(root/'current-standalone/formal-viewer.cjs')==read(root/'current-standalone/closed.json')['driver_sha256']
 return {p/n for n in rows}
