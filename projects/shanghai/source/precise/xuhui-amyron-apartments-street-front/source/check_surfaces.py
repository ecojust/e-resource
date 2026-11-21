"""Inspect the three meshes at round lights, folded windows, open balconies and the entrance canopy."""
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
ID='xuhui-amyron-apartments-street-front'
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
    from math import sqrt,hypot
    def curve(x):
        return .22+10-sqrt(100-x*x)
    def face(x):
        v=abs(x)
        return curve(x) if v<=3.76 else curve(3.76)+(v-3.76)*(.59 if x>0 else .45)
    def front(name,x,z,material,lo,hi,limit=13):
        ray(name,[x,-4,z],[0,1,0],limit,material,lo,hi)
    for n in (2,3,4,5):
        for x in [-2.17,-.39,1.16,2.63]:
            y=curve(x);z=n*3.28
            front('glazing along the curved street wall at '+str((n,x)),x,z+1.13,'slightly grey window glass',4+y+.15,4+y+.31)
            front('deep brick band below the ribbon at '+str((n,x)),x,z+.34,'warm ochre face tile',4+y-.035,4+y+.035)
    for n in (1,2,3,4):
        for x in [-5.31,5.34]:
            z=n*3.28;y=face(x)
            front('flank window '+str((n,x)),x,z+1.22,'slightly grey window glass',4+y+.14,4+y+.33)
            front('wing wall below window '+str((n,x)),x,z+.36,'warm ochre face tile',4+y-.055,4+y+.03)
    for x in (-3.34,3.34):
        front('two-storey jamb at sidewalk '+str(x),x,2.03,'warm ochre face tile',4.65,4.74)
    front('center clear to entrance',.34,1.1,None,0,6.29,limit=6.29)
    front('wood entrance leaf',.15,.71,'burgundy entrance timber',6.49,6.58)
    front('blue light inset into the timber leaf',.61,1.25,'slightly grey window glass',6.44,6.53)
    front('second-storey vestibule sash',.35,4.32,'slightly grey window glass',6.47,6.59)
    ray('clear floor-to-soffit height of entrance',[.25,.84,.2],[0,0,1],7,'shadowed tile in entrance',6.15,6.26)
    ray('roof of central six-storey body',[.10,1,22],[0,0,-1],5,'flat roof',1.61,1.72)
    for x in (-5.4,5.4):
        ray('tiered wing roof at '+str(x),[x,face(x)+.9,22],[0,0,-1],8,'flat roof',5.1,5.25)
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
