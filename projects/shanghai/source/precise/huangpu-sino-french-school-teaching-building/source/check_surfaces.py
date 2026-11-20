"""Independently probe the three courtyard projections, gallery depths and west street end."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-sino-french-school-teaching-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    import numpy as np
    rows=[]
    def probe(label,origin,direction,material,depth,tol=.043):
        hit=scene.ray(list(origin),list(direction),50)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<tol)
        rows.append(dict(label=label,origin=list(origin),direction=list(direction),reference_depth_m=depth,
                         expected_material=material,hit=hit,passed=ok))
    def facing(a,b):
        a,b=np.asarray(a,float),np.asarray(b,float)
        axis=(b-a)/np.linalg.norm(b-a)
        return (a+b)/2,axis,np.array([-axis[1],axis[0]]),np.linalg.norm(b-a)

    def front(face,u,z,material,depth,label):
        midpoint,axis,inward,_=face
        start=midpoint+axis*u-inward*2
        probe(label,[*start,z],[*inward,0],material,2+depth)

    def facade_bays(face,widths,recess):
        mid,axis,inside,total=face
        limits=np.r_[0,np.cumsum(widths)/sum(widths)]*total-total/2
        for a,b in zip(limits,limits[1:]):
            center=(a+b)/2
            for z in (2.02,6.48,11.42):
                front(face,center+.20,z,'grey green glass',recess+.30,'recessed gallery wall' if recess else 'projecting wing casement')
            if recess:
                # The detailed sash has an extra middle rail at this height.
                # In the simplified model the ray goes through to the glass.
                if role=='lod':
                    front(face,center+.20,6.72,'grey green glass',recess+.30,'simplified gallery lights')
                else:
                    front(face,center+.20,6.72,'dark stained window joinery',recess+.202,'gallery middle rail')
                front(face,center+.22,4.72+.96,'dark red gallery ironwork',.185-.055,'gallery rail crest')
                front(face,center+.20,4.72+.31,'warm ivory rendered stone',recess,'view under gallery rail to rear wall')

    # Exterior edges measured in the common WGS84 frame. The gallery depths below
    # are independently checked on packed meshes, including empty air above rails.
    for a,b in [((-42.43,.37),(-35.14,0)),((35.14,0),(42.43,-.37))]:
        facade_bays(facing(a,b),[1,1],0)
    central=facing((-14.37,.05),(14.37,-.05));mid,axis,_,length=central
    for l,r,pattern,recess in [(-length/2,-length/2+7.04,[1,1],0),
            (-length/2+7.04,length/2-7.04,[1,1.5,1],2.52),
            (length/2-7.04,length/2,[1,1],0)]:
        facade_bays(facing(mid+l*axis,mid+r*axis),pattern,recess)
    for a,b in [((-34.03,9.79),(-14.65,9.41)),((13.43,10.23),(34.65,10.05))]:
        facade_bays(facing(a,b),[.50,1.02,1.36,1.02,.50],2.52)
    # The southwest street end has five bays. Its four flankers are paired.
    west=facing((-41.51,24.08),(-42.43,.37))
    for i in range(5):
        center=-west[3]/2+(i+.5)*west[3]/5
        samples=[center+.24] if i==2 else [center-.76+.20,center+.76+.20]
        for u in samples:
            for z in [1.62,6.57,11.33]:
                front(west,u,z,'grey green glass',.30,'west end opening')
    for x,y,z in [(0,10,14.04),(-20,14,14.04),(20,15,14.04),(-1,17,15.22),(23,22,14.82)]:
        probe('flat roof or service coping',[x,y,22],[0,0,-1],'charcoal waterproofed roof',22-z)
    for x,y in [(-25,1),(-24,5),(24,1),(23,5),(-44,14),(44,18),(0,-3)]:
        probe('court recess or street outside old teaching block',[x,y,22],[0,0,-1],None,None)
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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
