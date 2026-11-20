"""Sample the actual serialized Metropole street corner; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-metropole-hotel'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    from math import hypot, radians, sin, cos
    rows=[]
    def shot(label,position,direction,material,expected):
        hit=scene.ray(position,direction,90)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-expected)<.065)
        rows.append(dict(label=label,origin=position,direction=direction,expected=material,expected_distance_m=expected,hit=hit,passed=passed))
    def on_wall(a,b,u,z,want,distance,label):
        dx=b[0]-a[0];dy=b[1]-a[1];length=hypot(dx,dy);tx=dx/length;ty=dy/length
        px=(a[0]+b[0])/2+u*tx;py=(a[1]+b[1])/2+u*ty
        shot(label,[px+ty*6,py-tx*6,z],[-ty,tx,0],want,distance)
    points=[(13.93*sin(radians(v)),13.93*(cos(radians(v))-1))for v in [-52.4,-39.4,-16.7,16.7,39.4,52.4]]
    for i,(a,b)in enumerate(zip(points,points[1:])):
        n=10 if i==2 else 9 if i in [1,3]else 8
        positions=[-2.04,0,2.04]if i==2 else [-1.13,1.13]if i in [1,3]else [0]
        for u in positions:
            for row in [0,n-1]:
                on_wall(a,b,u+.18,10.78+row*3.69,'blue grey glass',6.416,'lowest and highest square windows of each bay')
        if i==2:
            for u in positions:
                on_wall(a,b,u+.23,2.45,'blue grey glass',7.55,'three independently recessed entrance doors')
                on_wall(a,b,u+.20,7.23,'blue grey glass',6.416,'three arched mezzanine windows')
                on_wall(a,b,u+.20,50.01,'interior shadow',6.57,'three tall upper arched louvres')
            on_wall(a,b,.34,5.19,'aged bronze',3.74,'cantilevered bronze and glass canopy')
            on_wall(a,b,3.10,1.53,'polished granite',5.78,'stepped granite entrance jambs')
        if i in [1,3]:
            for u in positions:on_wall(a,b,u+.20,45.48,'interior shadow',7.30,'recess of the two upper shoulder galleries')
    for a,b,count in [((-20.76,4.03),points[0],5),(points[-1],(17.52,1.02),3)]:
        length=hypot(a[0]-b[0],a[1]-b[1]);
        for n in range(count):on_wall(a,b,(n-(count-1)/2)*length/count+.19,14.70,'blue grey glass',6.416,'eight lower street-window axes')
    canopy_y=points[2][1]+.78
    for x in [-2.04,2.04]:
        shot('pendant lantern under the recessed entrance ceiling',[x+.10,canopy_y-.03,2.15],[0,0,1],
             'canopy panels',1.62)
    for x,y,z in [(0,3,65.0),(8.1,2.0,48.12),(-10.85,2.3,43.05),(-12.2,4.6,32.35)]:
        shot('occupied and setback roof heights',[x,y,75],[0,0,-1],'grey roof',75-z)
    for x,y in [(0,-11),(24,3),(14,17),(-14,15),(0,24)]:
        shot('estate boundaries and roundabout open space',[x,y,75],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed'] for r in rows))

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
