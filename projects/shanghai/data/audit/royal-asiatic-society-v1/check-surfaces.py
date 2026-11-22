"""Trace the stone entrance, grille, window strips, crest and surrounding air."""
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
assert m['id']=='huangpu-royal-asiatic-society-huqiu-front'
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
    masonry=['buff facing brick','ochre facing brick','pale brick','buff brick joints']
    for x in [-4.45,4.45]:
        front('octagonal frame',x+.221,2.23,'brass window bars')
        front('upper trigram outer bar',x,2.23+.391,'brass window bars')
        front('central S divider',x,2.23,'brass window bars')
        front('open dark recess',x+.093,2.23-.037,'shadowed doorway')
        front('octagonal frame corner remains ashlar',x+.476,2.23+.44,'grey ashlar')
        front('museum plaque',x,1.27,'dark metal')
    for x in [-2.04,0,2.04]:
        front('arch void above the iron gate',x,2.32,'shadowed doorway')
        front('stone above the arch',x,3.38,'grey ashlar')
        front('stone outside the arched head',x+.70,3.05,'grey ashlar')
        front('gate lower rail',x,0.369,'dark metal')
        front('lowest entrance tread',x,.07,'grey ashlar')
    for x in [-2.03,0,2.03]:
        for z in [10.1,14.73,18.42]:
            front('recessed glass between uprights',x+.104,z,'blue-grey glass')
        for z in [12.54,16.62]:
            front('fluted metal panel below upper windows',x+.128,z,'dark metal')
    for hand in [-1,1]:
        front('outer high slit',hand*4.43,18.43,'blue-grey glass')
        front('outer wing brickwork',hand*5.47,12.56,*masonry)
        front('stone parapet panel',hand*4.42,21.54,'limestone edge','grained limestone')
        front('sky over lower end bay',hand*4.45,22.45,None)
        front('air outside the curb frontage',hand*6.79,6,None)
    front('balcony horizontal rail',.49,4.78,'limestone edge')
    front('thin capital above stepped central parapet',0,23.32,'limestone edge')
    front('R upright on crown panel',-.975,22.90,'grained limestone')
    front('A crossbar on crown panel',0,22.905,'grained limestone')
    front('S bottom stroke on crown panel',.775,22.75,'grained limestone')
    for x in [-4.415,4.415]:
        front('cartouche centre boss',x,21.46,'limestone edge')
        front('cartouche border',x+.897,21.45,'grained limestone')
    for x in [-3.54,-1.18,1.18,3.54]:
        ray('underside of curved balcony bracket',[x,-.54,3.18],[0,0,1],['grey ashlar'],.90)
    front('open sky over centre',0,23.6,None)
    out[variant]=dict(source_sha256=sha(packed),decoded_sha256=sha(path),triangles=len(scene.tri),checks=checks)
args.out.write_text(json.dumps(dict(id=m['id'],manifest_sha256=sha(args.manifest),variants=out),ensure_ascii=False,indent=2)+'\n')
print({k:len(v['checks'])for k,v in out.items()})
