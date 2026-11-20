"""Test the open steel windows, recessed dark portal, metal spandrels and stepped crown directly on all shipped meshes."""
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
ID='huangpu-development-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    import numpy as np
    edge=np.array([[-17.67,-.39],[-12.06,-5.70],[-5.16,-.66],[-3.23,-.14],[1.83,-.15],[3.87,-1.12],[9.83,-5.70],[16.18,1.02]])
    counts=[3,2,1,3,1,2,3];levels=[8,8,14,16,14,8,8]
    def ray(label,o,v,mat,d,tolerance=.037):
        h=scene.ray(o,v,90)
        passed=(h is None)if mat is None else h is not None and h['material']==mat and abs(h['distance_m']-d)<tolerance
        rows.append(dict(label=label,origin=o,direction=v,expected_material=mat,expected_distance=d,actual=h,passed=passed))
    def front(label,k,u,z,mat,projection):
        a,b=edge[k:k+2];t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);o=(a+b)/2+u*t+2*n
        ray(label,[*o,z],[-n[0],-n[1],0],mat,2-projection if projection is not None else None)
    glass='cool steel window glass';sash='black steel sash';metal='dark bronze spandrel'
    for k,(cols,storeys) in enumerate(zip(counts,levels)):
        length=np.linalg.norm(edge[k+1]-edge[k]);c=[0.]if cols==1 else [-1.54,0.,1.54]if k==3 else np.linspace(-length/2+length/(cols*2),length/2-length/(cols*2),cols)
        for u in c:
            if k!=3:front('granite base window',k,u+.17,2.10,glass,-.283)
            for j in range(storeys):
                z=10.84+3.49*j
                front('glazing in stepped window ribbon',k,u+.17,z+.67,glass,-.283)
                if j%3==0:front('upper steel transom',k,u+.19,z+2.20*.72+.022,sash,-.172)
                if j>0 and j%3==1:front('between-floor metal panel',k,u+.14,z-.62,metal,.023)
        front('aggregate parapet lip',k,.32,[39.12,39.12,60.19,66.89,60.19,39.12,39.12][k]-.11,'ochre cement rib',.11)
    l=np.linalg.norm(edge[4]-edge[3]);h=l/2
    for x in [-h+.14,-1.47,-.49,.49,1.47,h-.14]:
        front('raised fin on central stepped crown',3,x,67.59,'ochre cement rib',.14)
    front('dark frame at the entrance head',3,.31,9.58,'black granite portal',.275)
    front('central high vestibule glazing',3,.40,6.26,'bronze entrance glazing',-.865)
    front('lower recessed entry glazing',3,.43,1.62,glass,-1.02)
    front('polished entrance crossbar',3,-.47,3.12,'black granite portal',-.827)
    front('upper skylight beyond low return',0,0,65.1,None,None)
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
