"""Check the actual Continental Bank entrance, six tiers of fifteen windows, lamps, steps and raised lettering."""
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
MODEL = 'huangpu-continental-bank'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]

    def expect(label,origin,direction,material,depth=None):
        hit=scene.ray(origin,direction,30)
        passed=hit is None if material is None else (
            hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<.04)
        records.append({'label':label,'origin_m':origin,'direction':direction,
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':bool(passed)})

    p=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    width=p['registered_front_width_m']-.78
    front=.18
    def street(label,x,z,first_y,material):
        expect(label,[float(x),-2.,z],[0.,1.,0.],material,None if first_y is None else first_y+2)
    ratios=[.040,.131,.189,.264,.365,.403,.464,.504,.545,.603,.645,.738,.815,.870,.960]
    for i,a in enumerate(ratios):
        x=(a-.5)*width
        y=1.76 if abs(x)<4.78 else front
        for j,z in enumerate([9.88,12.98,16.07,19.18,22.28,25.41]):
            street(f'upper office window {i+1}, row {j+1}',x+.17,z+.76,y+.355,'recessed glass')
        street(f'window mullion {i+1}',x,23.08,y+.158,'bronze window frame')
    for ratio,z in [(-.461,4.22),(-.347,1.80),(-.242,1.80),(-.150,1.80),(.150,1.80),(.242,1.80),(.347,1.80),(.461,4.22)]:
        street('ground hall opening '+str(ratio),ratio*width+.13,z+1.42,front+.355,'bank glazing')
    for k in range(9):
        expect('entrance tread '+str(k+1),[.55,front+k*.255+.13,2.60],[0.,0.,-1.],'granite',2.60-(k+1)*.146)
    street('door recessed behind the central staircase',.28,2.50,front+2.095,'bank glazing')
    street('inner banking-hall transom',.20,7.04,front+1.81,'bank glazing')
    for u in [-2.41,2.41]:
        street('central bronze bar on octagonal lantern '+str(u),u,6.96,front-.893,'lantern bronze')
        street('lantern glass beside the bronze bar '+str(u),u+.083,6.96,front-.840,'lantern glass')
    street('Chinese sign fascia outside letters',1.91,8.98,front-.325,'granite')
    for q in [-.36,-.24,-.15,.15,.24,.36]:
        street('basement recess '+str(q),q*width+.12,.74,front+.37,'bank glazing')
    expect('inside rear closure',[0.,6.,32.],[0,0,-1],'roof',3.97)
    expect('empty foreground street',[0.,-1.4,1.9],[0,0,-1],None)
    expect('retained original rear office',[0.,16.0,1.9],[0,0,-1],None)
    for name in ['buff brick','ochre brick','sand brick','brown brick']:
        tri=scene.tri[scene.mi==scene.materials.index(name)]
        upper=tri[(tri[:,:,2].min(1)>9.28)&(tri[:,:,2].max(1)<25.051)]
        records.append({'label':'staggered north wall '+name,'triangles':len(upper),'passed':bool(len(upper)>150)})
    tri=scene.tri[scene.mi==scene.materials.index('sign bronze')]
    for name,low,hi,minc in [('111 on east jamb',2.60,3.15,30),('SITICO',8.19,8.49,150),('four Chinese sign characters',8.66,9.30,380)]:
        group=tri[(tri[:,:,2].min(1)>low)&(tri[:,:,2].max(1)<hi)]
        records.append({'label':name,'triangles':len(group),'passed':bool(len(group)>minc)})
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
