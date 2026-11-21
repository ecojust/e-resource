"""Check the photographed street section at the Clements west block against three delivered meshes."""
import argparse
import numpy as np
import math
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'xuhui-clements-apartments-west-front'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);results=[]
    p=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    def hit(name,origin,direction,wanted,limit=5):
        origin=list(map(float,origin));direction=list(map(float,direction))
        first=scene.ray(np.array(origin),np.array(direction),limit)
        allowed=[wanted] if isinstance(wanted,str)else wanted
        ok=first is None if allowed is None else bool(first and first['material'] in allowed)
        results.append({'name':name,'origin_author_m':origin,'direction':direction,'expected_first_material':allowed,'first_hit':first,'passed':ok})
    pts=np.asarray(p['street_path_xy'])
    for i,seg in enumerate((0,4)):
        a,b=pts[seg:seg+2];t=(b-a)/np.linalg.norm(b-a);w=np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);m=(a+b)/2
        sign=-1 if i==0 else 1
        def ray(name,u,z,expected):
            xy=m+t*u+n*.86;hit(f'Wing {i} {name}',(*xy,z),(*(-n),0.),expected,1.5)
        for column,u in enumerate((sign*w*.24,-sign*w*.265)):
            for level,z in enumerate((1.66,4.75,8.17,11.72)):
                ray(f'column {column} glass {level}',u+.14,z,'recessed green glass')
            ray(f'column {column} frame',u,7.84,'iron window grid')
            ray(f'column {column} mullion bay stripe',u+.78,7.04,'rust decoration')
        ray('ground plinth',.1,.32,'grey street plinth')
        ray('upper rough render',.08,8.11,'warm pebble render')
        xy=m+n*2
        hit(f'free street in front of wing {i}',(*xy,1.33),(0,0,-1),None,1.40)
        outer=sign*w*.24;ray('gable light',outer+.071,14.39,'recessed green glass')
        xx=min(a[0],b[0])+w*(.755 if i==0 else .245);yy=6.83 if i==0 else 8.05
        for j,dx in enumerate((-.43,0,.43)):
            hit(f'wing {i} dark open flue {j}',(xx+dx,yy,19),(0,0,-1),'flue opening',4)
        hit(f'wing {i} roof tiles',(xx+1.4,3.45,18.7),(0,0,-1),['burnt clay','tile terracotta'],5.6)
    for k in (1,3):
        a,b=pts[k:k+2];t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);w=np.linalg.norm(b-a)
        for i in range(3):
            c=(a+b)/2+t*(-w/2+(i+.5)*w/3+.085)+n*.8
            hit(f'court return {k} opening {i}',(*c,7.97),(*(-n),0),'recessed green glass',1.26)
    a,b=pts[1],pts[4];t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);c=(a+b)/2
    for name,offset,expected in [('private opening',2.57,None),('courtyard screen',-1.15,'warm pebble render')]:
        xy=c+t*offset+n*.80;hit(name,(*xy,1.31),(*(-n),0),expected,1.40)
    for x,y in ((.1,4.0),(3.2,7.0),(-2.7,4.77),(-22,1.67)):
        hit(f'open court or shared lane {x} {y}',(x,y,1.2),(0,0,-1),None,1.4)
    return {'triangles':len(scene.tri),'probes':results,'passed':sum(r['passed'] for r in results)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_bytes())
    assert manifest['id']==MODEL
    results={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            asset=manifest['assets'][role]
            path=args.manifest.parent/asset['file']
            assert path.stat().st_size==asset['bytes'] and digest(path)==asset['sha256']
            decoded=path
            if role!='raw':
                decoded=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,path,decoded,DECODER],check=True,stdout=subprocess.DEVNULL)
            results[role]=dict(sha256=asset['sha256'],file=path.name,**probes(decoded))
    report={'id':MODEL,'script_sha256':digest(Path(__file__)),'manifest_sha256':digest(args.manifest),
            'decoder_sha256':digest(DECODER),'reader_sha256':digest(READER),'results':results,
            'scope':'Checks only the sampled physical geometry in local axes; placement and viewing use independent records.'}
    assert all(r['passed']==len(r['probes']) and r['triangles']==manifest['assets'][role]['triangles'] for role,r in results.items())
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
