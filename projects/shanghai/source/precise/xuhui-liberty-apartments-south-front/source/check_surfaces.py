"""Inspect delivered central fins, paired windows, return glazing, wing spandrels, stepped roof and the entry."""
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
ID='xuhui-liberty-apartments-south-front'
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
    for i in range(1,9):
        z=3.57+(i-1)*3.05+.69
        for x in [-3.58,2.34]:
            ray(f'central window floor {i+1} x{x}',[x,-3,z+.76],[0,1,0],9,'blue grey glazing',3.26,3.36)
            ray(f'ivory reveal floor {i+1} x{x}',[x,-3,z+1.72],[0,1,0],9,'ivory cement',2.95,3.03)
        for sign,yfloor,xcenter in [(-1,4.58,-7.445),(1,4.27,7.19)]:
            ray(f'glazing on return floor {i+1} side {sign}',[sign*7,1.63,z+.75],[-sign,0,0],3,'blue grey glazing',1.9,2.01)
            if i<8:
                ray(f'set-back wing window floor {i+1} side {sign}',[xcenter+.36,-2,z+.72],[0,1,0],10,'blue grey glazing',2+yfloor+.18,2+yfloor+.27)
                ray(f'pale wing spandrel floor {i+1} side {sign}',[xcenter+.36,-2,z-.35],[0,1,0],10,'ivory cement',2+yfloor-.09,2+yfloor-.02)
    for x in [-.43,0,.43]:
        ray(f'free-standing rib above parapet {x}',[x,-3,29.20],[0,1,0],8,'ivory cement',2.72,2.90)
    for x in [-.88,.88]:
        ray(f'sky beside free-standing ribs {x}',[x,-2,29.20],[0,1,0],5,None)
    for y,z in [(0.22,.148),(.50,.280),(.9,.412)]:
        ray(f'entrance step {y}',[.11,y,1.55],[0,0,-1],2,'grey rough stone',1.55-z-.02,1.55-z+.02)
    ray('clear above steps to recessed wall',[0,-1,1.58],[0,1,0],2.45,None)
    ray('recess end behind three steps',[0,-1,1.58],[0,1,0],3,'shaded recess',2.49,2.57)
    for x,y,z in [(2,3,28.30),(-7,5.52,25.10),(7.07,5.42,25.10)]:
        ray(f'roof plain at {x} {y}',[x,y,31.45],[0,0,-1],8,'weathered roof',31.45-z-.025,31.45-z+.025)
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
