"""Probe both angled wings, the seven true arcade openings, tower, flue and north rooflights."""
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
MODEL = 'hongkou-lester-institute'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]
    par=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    plans=par['plans_m']
    levels=par['levels_m']

    def check(label,origin,direction,mat,dist=None,limit=12,tol=.052):
        origin=np.asarray(origin,dtype=float)
        direct=np.asarray(direction,dtype=float)
        hit=scene.ray(origin,direct,limit)
        ok=hit is None if mat is None else bool(hit and hit['material']==mat and
            (dist is None or abs(hit['distance_m']-dist)<tol))
        records.append({'label':label,'origin_m':origin.tolist(),'direction':direct.tolist(),
                        'material':mat,'distance_m':dist,'first_hit':hit,'passed':ok})

    def frame(a,b):
        a,b=np.asarray(a),np.asarray(b)
        axis=(b-a)/np.linalg.norm(b-a)
        return (a+b)/2,axis,np.array([axis[1],-axis[0]]),float(np.linalg.norm(b-a))

    def front(label,edge,u,z,mat,depth=None,limit=12):
        mid,axis,normal,_=edge
        start=mid+u*axis+.62*normal
        return check(label,[*start,z],[*-normal,0.],mat,None if depth is None else .62-depth,limit)

    for side in ('west','east'):
        e=frame(*plans[side][:2])
        step=e[3]/5
        for bay in range(5):
            for col in range(3):
                u=(bay-2)*step+(col-1)*.255*step
                for floor,(z,h) in enumerate(zip(levels['wing_main_window_bottoms'],levels['wing_main_window_heights'])):
                    name=f'{side} wing bay {bay+1} sash {col+1} floor {floor+1}'
                    front(name+' recessed pane',e,u+.14*(step*.185),z+.39*h,'reflective panes',-.326)
                    if col==1:
                        front(name+' narrow painted mullion',e,u,z+.39*h,'green steel',-.177)
    porch=frame(*plans['porch'][:2])
    step=porch[3]/7.15
    for col in range(7):
        front(f'open pointed arcade {col+1}',porch,(col-3)*step,2.34,None,limit=2.0)
        front(f'solid pointed crown over opening {col+1}',porch,(col-3)*step,5.75,'bush hammered stone',0)
    for col in range(6):
        x=(col-2.5)*step
        front(f'arcade pier {col+1}',porch,x,1.78,'bush hammered stone',0)
        front(f'carved shield in spandrel {col+1}',porch,x+.23,7.81,'granite trim',.12)
    for i in (1,3):
        s=frame(plans['porch'][i],plans['porch'][(i+1)%4])
        front('open arcade end '+str(i),s,0.,2.83,None,limit=1.7)
    check('continuous walking threshold to main doors',[0.,-8.67,1.0],[0,0,-1],'paving',.81)
    check('continuous roof joint along main block',[9.0,-8.67,8.0],[0,0,-1],'flat mineral roof',.66)
    center=frame(plans['center'][1],plans['center'][2])
    front('main door, timber leaf',center,.58,1.26,'dark oak',-.257)
    front('paired entrance astragal',center,0,1.60,'bronze shadow',-.172)
    for x in (-14.12,-11.92,11.92,14.12):
        front('upper central cheek '+str(x),center,x+.13,15.0,'reflective panes',-.326)
    loc=np.array([0.,-5.98])
    angles=np.linspace(-5*math.pi/8,11*math.pi/8,9)
    points=[loc+6.19*np.array([math.cos(t),math.sin(t)]) for t in angles]
    for i in (7,0,1):
        edge=frame(points[i],points[i+1])
        for z in (9.94,14.69,19.32,23.40):
            front(f'tower face {i}, window at {z}',edge,.23,z,'reflective panes',-.326)
    for k in (0,3,7,11):
        for offset,mat in [(0,'granite trim'),(.5,'lantern recess')]:
            theta=math.tau*(k+offset)/16
            radial=np.array([math.cos(theta),math.sin(theta)])
            check(f'crown radial sector {k} {mat}',[*list(loc+5.6*radial),27.50],[*list(-radial),0],mat)
    check('dark central flue vent',[.16,-5.97,36.0],[0,0,-1],'lantern recess',36-32.333)
    for j in range(3):
        floor=22.43 if j<2 else 22.36
        front_y=6.65+j*3.73
        for x in (-4.02,4.50):
            y=front_y+1.27
            top=floor+.13+(1.66-.13)*1.27/(3.73-.39)
            check(f'sawtooth slope {j+1} at {x}',[x,y,26.6],[0,0,-1],'flat mineral roof',26.6-top)
            check(f'northeast rooflight {j+1} at {x}',[x,front_y+4.38,floor+.91],[0,-1,0],'rooflight glazing')
    check('north flat hall roof',[7.98,36.,19.],[0,0,-1],'flat mineral roof',19.-13.91)
    for x,y in [(0.,-20.),(0.,-31.),(-21.,-18.),(15.,38.)]:
        check('unbuilt grounds '+str((x,y)),[x,y,5.],[0,0,-1],None)
    return {'triangles':len(scene.tri),'probes':records,'passed':all(r['passed']for r in records)}


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
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
