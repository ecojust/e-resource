"""Independently ray-test both rooftop towers, cornices, office windows and the theatre door."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-capitol-theatre'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    import numpy as np
    rows=[]
    def probe(label,origin,direction,material,depth,tol=.043):
        hit=scene.ray(list(origin),list(direction),50)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<tol)
        rows.append(dict(label=label,origin=list(origin),direction=list(direction),reference_depth_m=depth,
                         expected_material=material,hit=hit,passed=ok))
    def local(a,b):
        a,b=np.asarray(a,float),np.asarray(b,float);v=(b-a)/np.linalg.norm(b-a)
        return (a+b)/2,v,np.array([v[1],-v[0]])
    def face(label,center,t,n,x,z,material,depth):
        xy=center+t*x+n*2
        probe(label,[*xy,z],[-n[0],-n[1],0],material,2+depth)
    street=[(-26.19,10.38),(-25.99,5.82),(-23.64,1.27),(-21.07,-2.15),
            (-16.43,-5.87),(-9.50,-9.54),(-1.95,-12.92),(7.26,-14.56),(16.421,-15.77)]
    for i,(a,b) in enumerate(zip(street,street[1:])):
        c,t,n=local(a,b);w=np.linalg.norm(np.asarray(b)-a);count=max(1,round(w/2.14))
        for j in (0,count-1):
            u=(j+.5-count/2)*w/count
            for level in (0,3,6):
                face('rectangular steel-window recess',c,t,n,u+.13,3.99+3.25*level+1.16,'green-grey windows',.305)
        face('fourth-storey projecting stringcourse',c,t,n,.22,10.85,'limestone coping',-.46)
    c,t,n=local(street[3],street[4])
    face('former theatre door',c,t,n,.20,1.34,'smoked entrance glass',.60)
    face('open upper balcony front railing',c,t,n,.30,23.74+.78,'terrace iron',-.77)
    for idx,large in [(3,True),(7,False)]:
        c,t,n=local(street[idx],street[idx+1]);tw=c+(0 if large else 1.17)*t-(2.56 if large else 2.43)*n
        # The front of the principal and secondary towers faces the radial street.
        halfDepth=3.85/2 if large else 3.18/2
        face('recessed windows in rooftop plinth',tw+n*halfDepth,t,n,.18,28.17,'green-grey windows',.26)
        shaftDepth=2.62/2 if large else 2.46/2
        face('vertical tower opening',tw+n*shaftDepth,t,n,.16,37.9 if large else 31.8,'green-grey windows',.26)
        probe('principal finial' if large else 'secondary cap',[*tw,48],[0,0,-1],
              'lantern brass' if large else 'limestone coping',48-(41.75 if large else 34.71))
    for x,y in [(0,1),(10,4),(-9,1)]:
        probe('terrace behind curving facade',[x,y,44],[0,0,-1],'roof membrane',44-26.84)
    for x,y in [(0,13),(0,-17),(23,13)]:
        probe('adjoining building or street',[x,y,46],[0,0,-1],None,None)
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
