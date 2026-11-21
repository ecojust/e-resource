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
ID='xuhui-dauphine-apartments-garden-front'
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
    def forward(label,x,z,material,near,far,end=13):
        ray(label,[x,-5,z],[0,1,0],end,material,near,far)
    for level in (1,3,5,7,8):
        floor=3.22*level
        for sign in (-1,1):
            side='east' if sign>0 else 'west'
            forward(f'{side} circular light {level}',sign*5.08,floor+1.90,'blue grey window glass',6.59,6.63)
            forward(f'{side} actual circular rim {level}',sign*5.08,floor+2.228,'pale concrete coping',6.25,6.30)
            # Seen over the low parapet, this recess leads to actual glazing.
            forward(f'{side} balcony glazing {level}',sign*9.53,floor+1.36,'blue grey window glass',6.59,6.63)
            forward(f'{side} open air above the low parapet {level}',sign*9.53,floor+1.36,None,0,5.60,end=5.60)
            forward(f'{side} slab edge {level}',sign*10.2,floor-.07,'grey balcony slabs',3.93,3.99)
            forward(f'{side} concrete parapet {level}',sign*10.2,floor+.39,'sand toned wall render',3.93,4.00)
            forward(f'{side} tower crease sash {level}',sign*1.54,floor+1.49,'blue grey window glass',4.85,4.97)
            forward(f'{side} window pier under sash {level}',sign*1.79,floor+.28,'light rendered central bow',4.62,4.70)
    for z in (5.5,14.8,24.82,29.72):
        forward('unbroken central plaster pier '+str(z),.17,z,'light rendered central bow',4.58,4.62)
    forward('closed central entrance leaf',.34,1.76,'carefully recessed door',4.86,4.90)
    ray('underside over the entrance', [.77,-1.37,.82],[0,0,1],3,'warm cement soffit',1.94,1.98)
    ray('outside the rounded end of the canopy',[2.33,-1.95,.8],[0,0,1],2.62,None,0,2.62)
    for x in (-10,10):
        ray('top terrace slab '+str(x),[x,-.51,30.7],[0,0,-1],3,'grey balcony slabs',1.61,1.67)
        ray('open air past the balconies '+str(x),[x,-1.35,30.7],[0,0,-1],30,None,0,30)
    ray('flat central roof',[.04,2.14,31],[0,0,-1],4,'flat grey roof finish',1.43,1.52)
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
