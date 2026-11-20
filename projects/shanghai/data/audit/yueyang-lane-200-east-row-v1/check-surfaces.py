"""Sample the delivered ground, three-floor corner windows, staggered hoods and freestanding street fence."""
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
MODEL = 'xuhui-yueyang-lane-200-east-row'
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
    folds=np.asarray(p['front_xy_m']); glass=['blue gray glazing','shaded glazing']
    for k,(a,b) in enumerate(zip(folds,folds[1:])):
        bay=k//2+1;long=k%2==0
        length=np.linalg.norm(b-a);t=(b-a)/length;n=np.array([t[1],-t[0]]);mid=(b+a)/2
        left=-length/2+(.72 if long else .126);right=length/2-((.61 if bay in (1,3) else .47) if long else .105)
        if long and bay==5:right-=.15
        def cast(label,u,z,mat,outside=1.0):
            q=mid+t*u+n*outside
            hit(f'Bay {bay} {"front" if long else "return"} {label}',[*q,z],[*(-n),0],mat,outside+.50)
        for i,(floor,head)in enumerate(zip(p['estimated_floor_heights_m'],p['estimated_window_heads_m'])):
            if not long and bay==4:floor+=.08
            u=left+(right-left)*.614;prefix='level '+str(i+1)+' '
            cast(prefix+'glazing',u,floor+1.05,glass)
            cast(prefix+'bottom sill',u,floor-.072,'sunlit plaster ledges')
            cast(prefix+'projecting hood',u,head+.081,'sunlit plaster ledges')
            if long:
                count=4 if bay in (2,4)else 3
                cast(prefix+'vertical sash',left+(right-left)/count,floor+1.06,['dark sash','warm old sash'])
                cast(prefix+'latch or unbroken far pane',left+(right-left)*.72/count,(floor+head)/2,'aluminum sash' if len(scene.tri)>10000 else ('pale window curtain' if (bay,i)in [(2,1),(4,2),(5,0)] else glass))
            if long and (bay,i)in [(2,2),(3,1),(3,2),(4,2)]:
                cast(prefix+'outer drying rod',u,floor+.28,'terrace iron')
            if long and (bay,i)in [(2,1),(3,0),(4,1),(5,2)]:
                uc=right-.49 if bay%2 else left+.54
                cast(prefix+'condenser case',uc+.284,floor-.42+.148,'condenser cream')
        if long:
            q=mid+t*.2
            hit(f'Parapet covering at fold {bay}',[*q,15],[0,0,-1],'sunlit plaster ledges',3)
    rail=np.asarray([[-10.4,-10.25],[9.9,-2.55]]);unit=(rail[1]-rail[0])/np.linalg.norm(rail[1]-rail[0]);n=np.array([unit[1],-unit[0]])
    for i,q in enumerate(np.linspace(*rail,7)):
        hit(f'Street garden pier cap {i+1}',[*(q+np.array([.04,.015])),3.3],[0,0,-1],'yellow ochre masonry',2)
    for i in range(6):
        q=rail[0]+(rail[1]-rail[0])*(i+.5)/6
        hit('Fence horizontal metal bar '+str(i+1),[*(q+n*.7),1.37],[*(-n),0],'iron fence',1.3)
        hit('Fence ground curb '+str(i+1),[*(q+n*.7),.18],[*(-n),0],'gray plinth',1.3)
    for q in [(-7,-3.4),(0,-3.4),(3,-2.3),(0,-8.1),(14,0)]:
        hit('Open court or pavement '+str(q),[*q,15.0],[0,0,-1],None,16)
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
