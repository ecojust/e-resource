"""Probe the closed gates, both open galleries, public street sashes, curved inscription and upper tower."""
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
MODEL = 'hongkou-hongkew-fire-station'
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
            hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<.12)
        records.append({'label':label,'origin_m':origin,'direction':direction,
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':bool(passed)})

    def arc_y(x): return 6.62-.03158*x*x+.031*x
    bays=np.linspace(-8.6,8.6,5)
    def surface(a,b):
        a=np.array(a);b=np.array(b);t=(b-a)/np.linalg.norm(b-a);out=np.array([t[1],-t[0]])
        return (a+b)/2,t,out
    def ray_from(label,face,u,z,mat,depth):
        midpoint,t,out=face;q=midpoint+t*u+out*3
        expect(label,[*q,z],[*-out,0],mat,depth)
    def façade(a,b):return surface((a,arc_y(a)),(b,arc_y(b)))
    for i,(a,b) in enumerate(zip(bays,bays[1:])):
        f=façade(a,b)
        ray_from(f'closed gate {i+1} blue foot',f,.29,.62,'gate blue',3.1525)
        ray_from(f'closed gate {i+1} upper glazing',f,.24,2.78,'recessed glass',3.1475)
        for z in [6.78,11.05]:
            ray_from(f'open loggia {i+1} at {z} m',f,.05,z,'recessed glass',3+1.54*(-f[2][1])+.32)
        ray_from(f'repeated iron balcony badge {i+1}',f,0,5.40,'cast iron',2.7495)
    ring=np.array(json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())['source_uv_m'])
    for a,b,count,side in [(ring[15],ring[14],3,'Wusong street'),(ring[14],[-8.6,arc_y(-8.6)],2,'west wing'),([8.6,arc_y(8.6)],ring[10],2,'east wing')]:
        face=surface(a,b);step=np.linalg.norm(np.array(a)-np.array(b))/count
        for i in range(count):
            for z in [2.04,6.11,10.41]:
                ray_from(f'{side} sash {i+1} at {z}',face,(i+.5-count/2)*step+.25,z,'recessed glass',3.32)
    for z,mat,y in [(18.0,'recessed glass',16.39),(29.05,'dark opening',16.39)]:
        expect(f'upper lookout street face at {z}',[-.75,12,z],[0,1,0],mat,y-12)
    expect('apron outside the concave ground wall',[0,2,3],[0,0,-1],None)
    expect('separate east street wing beyond the cut',[25,15,40],[0,0,-1],None)
    expect('street roof outside the tower',[4,2,38],[0,0,-1],None)
    tris=scene.tri[scene.mi==scene.materials.index('cornice letters')]
    records.append({'label':'raised English lettering along the upper cornice','triangles':len(tris),'width_m':float(np.ptp(tris[:,:,0])),'passed':bool(len(tris)>500 and 7<np.ptp(tris[:,:,0])<7.7)})
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
