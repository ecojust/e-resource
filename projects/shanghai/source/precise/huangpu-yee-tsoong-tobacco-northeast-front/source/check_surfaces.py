"""Measure arched lights, closed storefronts, the cut corner, roof strips and the original rear building."""
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
ID='huangpu-yee-tsoong-tobacco-northeast-front'
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
    glass='muted blue glazing'
    trim='rose sandstone mouldings'
    brick='rose horizontal brickwork'
    dark='dark pressed spandrel'
    green='dark green door metal'
    left, right = -18.38+5.16,21.52-5.16
    pitch=(right-left)/7
    for i in range(7):
        x=(left+right)/2+(i-3)*pitch
        for y,wanted in [(6.15,glass),(9.2,dark),(11.2,glass),(12.22,glass),(13.85,trim)]:
            ray(f'north arch {i+1} height {y}',[x+.09,-2,y],[0,1,0],3,wanted)
        for dx in [-.61,.61]:
            ray(f'paired fourth floor windows {i+1}/{dx}',[x+dx+.16,-2,15.12],[0,1,0],3,glass)
        ray(f'attic light {i+1}',[x+.48,-2,18.12],[0,1,0],4,glass,2.94,3.13)
        if i==5:
            ray('rectangular entrance between the two high windows',[x+.26,-2,2.0],[0,1,0],3,green,2.56,2.62)
        else:
            ray(f'street shop window {i+1}',[x+.26,-2,2.0],[0,1,0],3,glass,2.32,2.39)
        if i in (4,6):
            ray(f'brick sill wall under western window {i+1}',[x+.22,-2,.95],[0,1,0],3,brick,1.97,2.05)
        ray(f'cream long-window field {i+1}',[x+1.61,-2,9.3],[0,1,0],3,'cream stucco long window field',1.97,2.04)
    def street_ray(label,a,b,u,z,material,lo=0,hi=4):
        p,q=np.array(a),np.array(b)
        tangent=(q-p)/np.linalg.norm(q-p)
        normal=np.array([tangent[1],-tangent[0]])
        p=(p+q)/2+u*tangent+2*normal
        ray(label,[*p,z],[*-normal,0.0],4,material,lo,hi)
    faces=[((-21.55,8.75),(-21.61,3.23),'east short return'),
           ((-21.61,3.23),(-18.38,0),'northeast cut corner'),
           ((-18.38,0),(-13.22,0),'north east shoulder'),
           ((16.36,0),(21.52,0),'north west end')]
    for a,b,name in faces:
        street_ray(name+' deep door',a,b,.17 if name=='north west end' else .4,1.63,green,2.36,2.46)
        for h in [6.62,10.73]:
            for x in [-.89,0,.89]:
                street_ray(name+f' narrow slots {h}/{x}',a,b,x+.08,h,glass,2.25,2.35)
        street_ray(name+' solid wall',a,b,1.67,8.67,brick,1.96,2.03)
        street_ray(name+' fourth floor paired window',a,b,.62,15.02,glass,2.25,2.36)
        street_ray(name+' cornice lip',a,b,.55,17.66,trim,1.10,1.21)
    ray('roof strip behind main fascia',[4,1.37,22],[0,0,-1],5,'grey roof covering',2.78,2.90)
    ray('original courtyard outside new mesh',[4,7,20],[0,0,-1],24,None)
    ray('original Huqiu facade beyond new return',[-22,12,6],[1,0,0],7,None)
    ray('street surface outside new fascia',[-2,-2,18],[0,0,-1],20,None)
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
