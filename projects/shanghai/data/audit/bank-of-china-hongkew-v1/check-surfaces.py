"""Test the actual southwest apartment arc, its seven storeys, stone ribbons, projecting piers and awnings."""
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
MODEL = 'hongkou-bank-of-china-hongkew'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]

    def expect(label,origin,direction,wants,interval=None):
        h=scene.ray(origin,direction,32)
        if wants is None:ok=h is None
        else:ok=h is not None and h['material'] in wants and (interval is None or interval[0]<h['distance_m']<interval[1])
        records.append({'label':label,'origin':np.asarray(origin).tolist(),'direction':np.asarray(direction).tolist(),'wanted':wants,'depth_m':interval,'first_hit':h,'passed':bool(ok)})
    cx=-4.35;cy=4.37;radius=5.35;start=-12.4;front=-.98
    straight=(cx-start)/3.;angular=math.radians(95)/4
    for i in range(7):
        curved=i>=3
        width=radius*angular if curved else straight
        def point(u):
            if not curved:
                return np.array([start+straight*(i+.5)+u,front]),np.array([0.,-1.])
            angle=angular*(i-3+.5)+u/radius
            normal=np.array([math.sin(angle),-math.cos(angle)])
            return np.array([cx,cy])+radius*normal,normal
        def street(name,u,z,wants,interval=None):
            q,n=point(u);origin=np.array([*(q+3.*n),z]);direction=np.array([*(-n),0.])
            expect(('curved' if curved else 'straight')+' '+str(i+1)+' '+name,origin,direction,wants,interval)
        for k,bottom in enumerate([.13,3.18,5.98,8.91,11.63,14.35,17.07]):
            street('storey '+str(k+1)+' sash interior',width*.11,bottom+.49,['lower glass']if k<3 else ['recessed glass'],(3.25,3.43))
        for z in [5.36,8.23]:
            street('deep red wrap '+str(z),0,z,['deep red brick'],(2.84,3.03))
        for z in [11.09,13.81,16.53]:
            # One visible air conditioner partially covers one of the square tiles.
            behind_awning=(i,z)in {(0,11.09),(0,13.81),(1,16.53),(2,13.81)}
            expects=['carved pale stone','condenser grille','grey condenser']if i==5 and z==11.09 else ['carved pale stone']
            street('spandrel first surface '+str(z),.060,z,['maroon canvas']if behind_awning else expects)
            if behind_awning:
                q,normal=point(.060)
                expect('square behind canopy at bay '+str(i+1)+' height '+str(z),[*((q+.14*normal)),z],[*(-normal),0.],['carved pale stone'],(.04,.11))
        street('tall four-storey string pier',-width/2+.065,14.88,['warm brick','buff stone'],(2.69,2.83))
        street('crowning pale cornice',width*.20,19.77,['carved pale stone'],(2.78,2.93))
        street('top roof edge',0,20.18,['deep red brick'],(2.52,2.68))
        if i<3:
            j=next(j for j in range(4)if (j+i)%3==0)
            street('curved maroon canopy',width*.15,8.91+j*2.72+1.72+.22,['maroon canvas'])
    expect('public street remains clear',[-10.,-2.4,1.9],[0.,0.,-1.],None)
    expect('unmodeled original apartment rear',[-10.,6.,1.9],[0.,0.,-1.],None)
    expect('anonymous eastern terminal 2701 remains separate',[4.,6.,1.9],[0.,0.,-1.],None)
    expect('shallow rooftop inside the western strip',[-9.,.40,28.],[0.,0.,-1.],['roof'],(7.85,8.05))
    return dict(triangles=len(scene.tri),probes=records,passed=all(r['passed'] for r in records))


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
