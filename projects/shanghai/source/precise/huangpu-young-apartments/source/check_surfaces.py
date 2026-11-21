"""Measure the curved bank storefront, glazed bays, iron railings and double roof on the actual three meshes."""
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
ID='huangpu-young-apartments'
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
    from math import sin,cos,radians
    radius=5.7668
    def polar(a,r):
        return np.array([r*sin(radians(a)),-r*cos(radians(a))])
    edges=[-61.841,-42,-16,16,42,62.3621]
    for i,(a,b) in enumerate(zip(edges,edges[1:])):
        begin,end=polar(a,radius),polar(b,radius)
        tangent=(end-begin)/np.linalg.norm(end-begin)
        normal=np.array([tangent[1],-tangent[0]])
        middle=(begin+end)*.5
        def front(label,offset,z,wanted,depth):
            target=middle+tangent*offset+normal*1.55
            ray(f'bay {i+1} {label}',[*target,z],[*-normal,0],3,wanted,*depth)
        for z in [1.02,5.47,8.82,12.32,15.73,19.45]:
            front('glazing '+str(z),.17,z,'grey blue plate glass',(1.83,1.90))
        front('bank shop transom',.17,.12+3.22/(2 if role=='lod' else 3),'blackened steel sash',(1.68,1.85))
        for z in [8.94,12.41,15.99]:
            # Vertical glazing members differ between the central three-column
            # bay and the remaining two-column windows.
            offset=0 if i!=2 else .82*np.linalg.norm(end-begin)/6
            front('sash '+str(z),offset,z,'blackened steel sash',(1.68,1.85))
    for z in [7.45,10.96,14.44]:
        r=(radius+.65 if z==7.45 else radius+.24)-.075
        for a in [-31,7,29]:
            v=polar(a,1)
            ray('iron top rail '+str((z,a)),[*(v*(r+.75)),z+1.0],[*-v,0],1.25,'black iron railing',.67,.84)
    for x,y,material,z,near,far in [(0,-3.,'weathered red roof tile',29.,1.95,3.2),
            (0,-.30,'weathered red roof tile',29.,.89,1.09),
            (-6.,1.5,'roof zinc',23.,1.10,1.15),
            (0,-7.4,None,1.8,0,3)]:
        ray('vertical section '+str((x,y)),[x,y,z],[0,0,-1],4,material,near,far)
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
