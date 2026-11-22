"""Trace photographed openings, glazing, oriel, paired circular hoods, end wings and open air."""
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
assert m['id']=='huangpu-ampire-and-co-building'
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
    for x in [-8.72,-5.72,-2.77,2.77,5.72,8.72]:
        for z in [1.47,5.49,9.48,12.83]:
            front('glazed opening',x+.16,z+.43,'blue-grey glass')
            front('individual dressed sill',x,z-.048,'weathered buff stone')
        front('shop awning',x,3.405,'patinated metal')
        front('stone key above second-floor arch',x,11.46,'pale carved stone')
    for x in [-5.72,5.72]:
        front('semi-circular hood',x+.21,8.59,'weathered buff stone')
        front('horizontal hood shelf',x,8.10,'weathered buff stone')
        front('triangular gable field',x,15.58,'red face brick')
        front('vertex of raking cornice',x,16.51,'weathered buff stone')
    front('oriel glazing',.15,10.83,'blue-grey glass')
    front('oriel stone corbel',0,9.65,'pale carved stone')
    front('stone key over entrance',.02,3.99,'pale carved stone')
    front('deep glazing of entry',.42,1.14,'blue-grey glass')
    front('upper window to central tower',.16,14.09,'blue-grey glass')
    front('tower cornice',0,16.68,'weathered buff stone')
    for side in (-1,1):
        for angle in [-.292*math.pi,0,.292*math.pi]:
            x=side*13.33+2.67*math.sin(angle)
            y=1.62-2.67*math.cos(angle)
            for z in [2.24,6.18,10.17]:
                ray('three radial windows at each level', [x+math.sin(angle)*1.75+.14*math.cos(angle), y-math.cos(angle)*1.75+.14*math.sin(angle),z],
                    [-math.sin(angle), math.cos(angle),0], ['blue-grey glass'])
        front('wing masonry between windows',15.17*side,7.90,'red face brick','ochre brick','dark face brick')
        front('curved end-wing belt',14.43*side,8.94,'weathered buff stone')
        front('lane outside end of model',16.9*side,6.12,None)
    ray('open air above middle cornice',[2.67,-2,15.90],[0,1,0],[None])
    out[variant]=dict(source_sha256=sha(packed),decoded_sha256=sha(path),triangles=len(scene.tri),checks=checks)
args.out.write_text(json.dumps(dict(id=m['id'],manifest_sha256=sha(args.manifest),variants=out),ensure_ascii=False,indent=2)+'\n')
print({k:len(v['checks'])for k,v in out.items()})
