"""Measure the public street frontage, open court, porches and roofs on all three general office meshes."""
from argparse import ArgumentParser
import numpy as np
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-jiangnan-historic-general-office'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,point,direction,length,wanted,lo=0,hi=20):
        hit=scene.ray(point,direction,length)
        ok=hit is None if wanted is None else bool(hit and hit['material']==wanted and lo<=hit['distance_m']<=hi)
        rows.append(dict(test=label,origin=list(map(float,point)),direction=list(map(float,direction)),length_m=length,expected_material=wanted,range_m=[lo,hi],hit=hit,passed=ok))
    # External samples refer to the south face, roof breaks and courtyard in the public-source plan.
    # Gate positions are checked independently of the author's opening objects.
    left,right=-46.15,43.38
    centers=[left+.8+(i+.5)*(right-left-1.6)/41 for i in range(41)]
    door_positions=(-22.,3.1,36.75)
    front=lambda label,x,z,want,interval:ray(label,[x,-21.9,z],[0,1,0],7,want,*interval)
    for k,x in enumerate(centers):
        if min(abs(x-u)for u in door_positions)<3.1:
            continue
        for z in (1.38,5.45):
            front(f'south opening {k} glazing at {z}m',x+.23,z,'grey reflective window glass',(4.54,4.60))
        front(f'south opening {k} plaster pier',x+.78,5.45,'pale rendered masonry',(4.23,4.27))
        if k % 3==0:
            z=5.13+(7.49-5.13)/(2 if role=='lod' else 3)
            front(f'south opening {k} timber transom',x+.20,z,'painted timber sash',(4.38,4.44))
    for x in (-22.,36.75):
        for side in (-1,1):
            front(f'entry {x} projecting pier {side}',x+side*1.95,1.70,'pale rendered masonry',(2.14,2.21))
        ray('canopy underside '+str(x),[x+.85,-18.7,2.72],[0,0,1],1,'pale rendered masonry',.44,.50)
        front('entrance timber leaves '+str(x),x+.60,.90,'brown entrance joinery',(4.47,4.53))
        ray('entrance stair '+str(x),[x,-19.,1.2],[0,0,-1],1.5,'carved pale stone',.69,.96)
    for i,(x,y,low,high) in enumerate([(2,-14,2.,6.),(-40,16.,1.,5.),(39,17.,2.,6.)]):
        hit=scene.ray([x,y,14],[0,0,-1],9)
        rows.append(dict(test='pitched roof '+str(i+1),point=[x,y,14],hit=hit,
                         passed=bool(hit and hit['material'] in ('weathered terracotta tile','fired tile lips') and low<hit['distance_m']<high)))
    for x,y in [(-18.,5.),(0.,15.),(17.,22.)]:
        ray('open north courtyard '+str((x,y)),[x,y,17.],[0,0,-1],17.3,None)
    return dict(passed=all(x['passed']for x in rows),samples=rows)


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
