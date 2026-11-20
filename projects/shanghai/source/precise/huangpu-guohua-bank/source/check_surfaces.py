"""Inspect the eight levels of the entrance tower, the two three-bay bows, radiating fan, stairs and four raised tablets."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from math import sin,cos,pi,hypot
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-guohua-bank'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,material,position,tolerance=.040):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-position)<tolerance
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=material,expected_distance=position,actual=hit,passed=passed))
    def front(label,x,z,material,y,tolerance=.040):
        sample(label,[x,-3,z],[0,1,0],material,3+y if y is not None else None,tolerance)
    for x in [-1.57,0,1.57]:
        for z in [11.85,15.87,19.89,23.91,27.93,31.95,35.97,39.99]:
            front('upper tower glazing in one of three vertical stacks',x+.18,z+.72,'smoky blue glass',.29)
            front('steel transom in upper tower',x+.21,z+2.12*.72,'dark steel sash',.233)
    curves=[((-9.96,4.56),(-8.22,.74),(-4.57,0)),((4.57,0),(8.02,-.94),(10.66,2.0))]
    def at(curve,t):
        return [(1-t)**2*curve[0][i]+2*t*(1-t)*curve[1][i]+t*t*curve[2][i]for i in [0,1]]
    for curve in curves:
        for i in range(3):
            a,b=at(curve,i/3),at(curve,(i+1)/3);dx,dy=b[0]-a[0],b[1]-a[1];length=hypot(dx,dy);tx,ty=dx/length,dy/length;nx,ny=ty,-tx
            u=(a[0]+b[0])/2+.19*tx;v=(a[1]+b[1])/2+.19*ty
            for z in [2.7,7.7,12.56,16.56,20.60,24.63,28.64,32.65,36.70]:
                sample('glazing on curved street shoulder',[u+2*nx,v+2*ny,z],[-nx,-ny,0],'smoky blue glass',2.29)
    for x in [-1.38,1.38]:front('recessed small attic opening',x,46.42,'dark steel sash',.32)
    for x in [-4.22,4.22]:front('outer tower rib',x,26,'weathered grey granite',-.24,.03)
    spring=7.0
    for k in [3,5,7,9,11,13,15]:
        a=k*pi/18;front('radial iron fanlight spoke',1.25*cos(a),spring+1.25*sin(a),'black patinated iron',.094)
    for k in [4.45,8.45,12.45]:
        a=k*pi/18;front('glazing between wrought iron spokes',1.29*cos(a),spring+1.29*sin(a),'smoky blue glass',.27)
    front('upper metal gate transom',.63,6.84,'black patinated iron',.045)
    for x in [-2.04,-.68,.68,2.04]:front('projecting square block for each character',x-.575,11.15,'light grey cut granite',-.142)
    for x,z in [(-2.29087,11.09787),(-.45402,11.29290),(.63445,11.33992),(1.64080,11.08520)]:
        front('raised brass glyph on restored right-to-left name tablet',x,z,'aged brass',-.219,.022)
    front('recessed public entrance glazing',.76,2.74,'smoky blue glass',1.66)
    for i in range(8):sample('exterior granite stair tread',[.88,.08+.196*i,1.42],[0,0,-1],'light grey cut granite',1.42-.142*(i+1))
    sample('roof of the central tower cut',[0,1.6,52],[0,0,-1],'plain section',52-48.77)
    for x,z in [(-11.4,4),(11.5,4)]:front('open street beyond the modeled section',x,z,None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


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
