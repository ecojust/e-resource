"""Read all three delivered meshes and inspect the wing bands, tower windows and five parapet blades."""
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
ID='jingan-medhurst-apartments'
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
    ends=np.array([[-29.16,3.56],[-16.34,-5.22],[-6.674,0],[6.674,0],[18.25,-6.88],[27.29,-.70]])
    ends[0]+=(ends[1]-ends[0])/np.linalg.norm(ends[1]-ends[0])*1.16
    ends[-1]+=(ends[-2]-ends[-1])/np.linalg.norm(ends[-2]-ends[-1])*.7
    for i,(a,b) in enumerate(zip(ends,ends[1:])):
        w=np.linalg.norm(b-a);axis=(b-a)/w;normal=np.array([axis[1],-axis[0]])
        center=(a+b)/2
        def at(label,u,z,material,lo,hi):
            origin=center+axis*u+normal*6
            ray(label,[*origin,z],[*-normal,0],9,material,lo,hi)
        mid_floor=center-normal*2.26+axis*.31
        zroof=38.82 if i==2 else 29.54
        ray('physical roof at level change '+str(i),[*mid_floor,zroof+2],[0,0,-1],4,'warm grey roof surface',1.99,2.01)
        shops=max(2,round(w/3.7));step=(w-.84)/shops
        xm=-w/2+.42+.5*step
        at('ground shop light '+str(i),xm+.167*step,1.43,'dark ground glass',6.25,6.29)
        at('projecting shop fascia '+str(i),.21,3.52,'pale grey cement cap',5.86,5.90)
        if i==2:
            for x in (-4.57,4.57):
                for r in (0,3,7,9,10):
                    at('tower sash '+str((x,r)),x+.37,4.08+r*3.1+1.19,'grey blue window glass',6.25,6.29)
            for x in (-1.74,-.87,0,.87,1.74):
                at('upright at seventh storey',x,23.75,'light stepped moulding',5.79,5.83)
                at('projecting upper upright',x,32.17,'pale grey cement cap',5.435,5.475)
                at('exposed blade above parapet',x,39.53,'light stepped moulding',5.435,5.475)
                at('open air next to blade',x+.31,39.87,None,0,9)
            at('roof cornice lamination',4.2,37.843,'light stepped moulding',5.75,5.80)
        else:
            count=4 if w>13.5 else 3
            step=(w-.75)/count;xc=-w/2+.375+.5*step;post=-w/2+.375+step
            for r in (1,3,6,7):
                z=4.08+r*3.1;sill=z+.48
                at('ribbon window glazing '+str((i,r)),xc+.078*step,sill+.83,'grey blue window glass',6.25,6.29)
                at('white band above dark ribbon',post,z+2.73,'warm ivory cement',5.985,6.015)
                at('umber tile between sashes',post,sill+.824,'dark umber glazed tile',5.985,6.015)
            at('lowest projecting cornice blade',.37,29.54-.75,'light stepped moulding',5.81,5.85)
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
