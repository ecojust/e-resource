"""Check the windows, slabs, doors and stair tower on the two public elevations."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from math import sin,cos,pi,hypot
import numpy as np
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-chekiang-first-commercial-bank'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    R=np.array([[cos(32*pi/180),-sin(32*pi/180)],[sin(32*pi/180),cos(32*pi/180)]])
    ref=np.array([-11.81246,7.38124])
    C=np.array([-33.15233,11.16454]);W=np.array([-22.02035,0]);N=np.array([-34.78759,32.15649]);S=np.array([22.02031,0])
    U=(N-C)/np.linalg.norm(N-C);T=C+9.52*U
    glass='blue grey window glass';shade='buff exposed aggregate sunshade';steel='dark rolled steel sash'
    def ray(label,origin,direction,material,distance,tolerance=.036):
        o=np.array(origin,dtype=float);o[:2]=(o[:2]-ref)@R.T;v=np.array(direction,dtype=float);v[:2]=v[:2]@R.T
        hit=scene.ray(o.tolist(),v.tolist(),65)
        success=hit is None if material is None else hit is not None and hit['material']==material and abs(distance-hit['distance_m'])<tolerance
        rows.append(dict(label=label,origin=o.tolist(),direction=v.tolist(),expected_material=material,expected_distance=distance,actual=hit,passed=success))
    def facade(label,edge,u,z,mat,front):
        a,b=edge;d=(b-a)/np.linalg.norm(b-a);n=np.array([d[1],-d[0]]);origin=(a+b)/2+u*d+3*n
        ray(label,[*origin,z],[-n[0],-n[1],0],mat,3-front)
    rows_z=[(7.20,2.13),(10.06,1.71),(13.27,2.05),(17.04,2.02),(20.97,2.08),(25.15,2.02),(30.28,2.13)]
    for i,(z,h) in enumerate(rows_z):
        l=-22.02033+(.86 if i==6 else .10);r=22.02033-.35
        for cell in range(7):
            x=l+(cell+.376)*(r-l)/7
            facade('window in one of seven Jiangxi ribbon levels',(W,S),x,z+.46,glass,-.31)
        facade('projecting west sunshade',(W,S),-5,z+h+.18,shade,.62)
        facade('intermediate west shading rail',(W,S),6,z+.78,shade,.33)
    for i in [-3,-2,-1,1,2,3]:
        facade('one of the six large bank hall lights',(W,S),i*5.56+.37,3.20,glass,-.31)
    facade('recessed bank door glazing',(W,S),.27,1.81,glass,-1.357)
    facade('bronze bank door transom',(W,S),.37,2.73,'aged bronze portal',-1.315)
    facade('western blue fascia',(W,S),7.3,6.40,'blue street fascia',.42)
    for i in range(3):
        ray('one of three stone treads',[.62,.20+.25*i,.85],[0,0,-1],'polished Jinshan stone',.85-.14*(i+1))
    half=np.linalg.norm(W-C)/2
    for z,h in rows_z[:6]:
        for u in [-.51,4.28]:
            facade('splayed two-bay strip glazing',(C,W),u,z+.44,glass,-.31)
        facade('splayed wall punched light',(C,W),-half+2.47,z+.46,glass,-.31)
        facade('outside corner shading slab',(C,W),2.80,z+h+.18,shade,.62)
    facade('corner attic window',(C,W),half-2.27,31.03,glass,-.31)
    x=9.52/2-3.20
    for z in [8.67,12.60,16.73,20.96,25.12,29.17]:
        facade('north stair tower glazing',(T,C),x+.39,z,glass,-.34)
        facade('stair tower vertical bars',(T,C),x+.765,z,shade,.196)
    facade('north bronze door leaf',(T,C),x+.32,1.45,'aged bronze portal',-.71)
    for z,h in rows_z[:4]:
        facade('lower Hankou wing glazing',(N,T),1.08,z+.44,glass,-.31)
        facade('lower wing shading slab',(N,T),.27,z+h+.18,shade,.62)
    for u in [-6.,-.62,5.4]:
        ray('roof strip at western parapet',[u,1.21,38],[0,0,-1],'plain section',2.90)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(q['passed']for q in rows))


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
