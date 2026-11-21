"""Trace the visible street openings, plaque, cornice and cut roof profile."""
import argparse
import hashlib
import json
import runpy
import math
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--decoded',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
project=Path(__file__).resolve().parents[3]
Scene=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
m=json.loads(args.manifest.read_bytes())
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
assert m['id']=='xuhui-huaihai-road-1768-residence'
out={}
for variant in ('raw','full','lod'):
    item=m['assets'][variant]
    packed=args.manifest.parent/item['file']
    path=packed if variant=='raw' else args.decoded/(variant+'.glb')
    assert sha(packed)==item['sha256']
    scene=Scene(path);checks=[]
    def ray(label,origin,direction,allow,dist=7):
        hit=scene.ray(origin,direction,dist);mat=(hit or {}).get('material')
        checks.append({'name':label,'origin':origin,'direction':direction,'distance_m':dist,'expected':allow,'actual':mat})
        assert mat in allow,(label,hit)
    def front(label,x,z,*materials):
        ray(label,[x,-2,z],[0,1,0],list(materials))
    for bottom,height,rise in [(4.07,1.85,0),(7.23,1.65,.28)]:
        for fraction in [-.305,-.160,.142,.285]:
            x=fraction*9.48946
            front('inset upper glazing',x+.105,bottom+.95,'muted glazing')
            front('opening jamb',x+.401,bottom+height-.46,'weathered stone moulding')
            front('shared window ledge',x,bottom-.071,'weathered stone moulding')
    front('left ground panel',-2.02,.92,'muted glazing')
    front('right ground panel',2.095,.94,'muted orange panel')
    for x in [-2.05,2.12]:front('segmental ground head',x,2.819,'pink-grey stone base')
    front('enamel lane number background',-4.444,2.432,'green lane plaque')
    front('stone heritage plaque',-4.15,1.91,'pink-grey stone base')
    front('cornice at ground-floor head',.05,3.30,'weathered stone moulding')
    front('cornice below roof',.08,10.82,'weathered stone moulding')
    ray('central near roof',[1.0,4.39,20],[0,0,-1],['weathered red roof tile'],12)
    ray('south lane off house',[-6,-1.0,20],[0,0,-1],[None],25)
    ray('area outside manor frontage',[3,-1.0,16],[0,0,-1],[None],22)
    out[variant]=dict(source_sha256=sha(packed),decoded_sha256=sha(path),triangles=len(scene.tri),checks=checks)
args.out.write_text(json.dumps(dict(id=m['id'],manifest_sha256=sha(args.manifest),variants=out),ensure_ascii=False,indent=2)+'\n')
print({k:len(v['checks'])for k,v in out.items()})
