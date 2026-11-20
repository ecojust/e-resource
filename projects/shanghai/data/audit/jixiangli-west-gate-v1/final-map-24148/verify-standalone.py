"""Verify the four original viewer photos and each input actually delivered by the current site."""
from pathlib import Path
import hashlib
import json
from urllib.request import urlopen

live=Path('/workspace/e-resource/projects/shanghai')
audit=live/'data/audit/jixiangli-west-gate-v1'
w=Path(__file__).parent
frozen=Path('/tmp/jixiang185/projects/shanghai')
scene=Path('/tmp/shanghai-east-medical-focus/scenes/148-production.json')
def read(p):return json.loads(p.read_bytes())
def digest(b):return hashlib.sha256(b).hexdigest()
viewer=read(audit/'viewer.json')
signed=read(scene)
folder='assets/models/candidates/'+viewer['id']+'/'
expected={**viewer['files'],folder+'manifest.json':viewer['manifestSHA256'],**{folder+v['file']:v['sha256'] for v in viewer['downloads'].values()}}
assert viewer['passed'] and viewer['pageErrors']==[] and len(viewer['views'])==4
assert set(viewer['downloads'])=={'raw','full','lod','native'}
records={}
base='http://127.0.0.1:24148/'
for k,h in expected.items():
 with urlopen(base+k,timeout=90)as r:body=r.read();assert r.status==200
 assert digest(body)==digest((frozen/k).read_bytes())==h==signed['files'][k]
 records[k]={'http':200,'bytes':len(body),'sha256':h}
photos={}
for view in viewer['views']:
 path=audit/view['filename'];assert digest(path.read_bytes())==view['sha256'];photos[path.name]=dict(bytes=path.stat().st_size,role=view['role'],viewport=view['viewport'],sha256=view['sha256'])
proof=dict(original_route=viewer['base']+viewer['route'],verified_current_site=base,source_report_sha256=digest((audit/'viewer.json').read_bytes()),signed_scene_sha256=digest(scene.read_bytes()),original_browser=viewer['browser'],current_input_files=records,original_photos=photos)
(w/'independent-viewer-24148.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
print(len(records),len(photos))
