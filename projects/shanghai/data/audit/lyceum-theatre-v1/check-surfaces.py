"""Probe the three finished meshes for the three street arches, upper three windows, five-letter sign, marquee and stepped auditorium roofs."""
import argparse
import math
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'huangpu-lyceum-theatre'
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
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})

    front=-22.90;center=(-10.47+8.34)/2
    def street(label,u,z,material,depth):
        expect(label,[center+u,front-2,z],[0,1,0],material,depth)
    for i,u in enumerate([-4.14,0,4.14]):
        street(f'entrance door {i+1}',u+.31,2.31,'bronze and glazed door',2.33)
        street(f'arched upper glass {i+1}',u+.46,10.08,'smoked blue glass',2.33)
        street(f'arch keystone {i+1}',u,12.83,'warm artificial stone',1.71)
    for i,u in enumerate([-2.76,0,2.76]):
        street(f'top rectangular window {i+1}',u+.40,15.61,'smoked blue glass',2.33)
    street('projecting upper balcony',0,14.04,'warm artificial stone',1.065)
    street('west corner stone',-9.1,15.48,'pale projecting stone',1.87)
    for i,(dx,dz) in enumerate([(-.2541,.4838),(.1328,.4491),(-.0853,.0023),(-.3264,-.0402),(.2361,.4299)]):
        expect('gold sign '+'兰心大戏院'[i],[center+(i-2)*3+dx,front-2.40,5.84+dz],[0,1,0],'gilded metal lettering',.62)
    expect('marquee top',[center+1.5,front-1.30,8],[0,0,-1],'patinated black iron',2.97)
    expect('walkable entrance below canopy',[center+1.5,front-1.30,2],[0,0,1],'marquee underside',2.565)
    expect('main entrance flat roof',[center,-17.16,30],[0,0,-1],'charcoal roofing',11.03)
    expect('barrel roof crown',[-2.85,-4.52,30],[0,0,-1],'blue grey sheet metal',13.14)
    expect('raised stagehouse roof',[-3.7,11.50,30],[0,0,-1],'charcoal roofing',6.67)
    expect('outside chamfered entrance',[center,-26.75,22],[0,0,-1],None)
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
