"""Check five glazed strips, neighboring piers, three doors, marquee and roof in every delivered GLB."""
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
MODEL = 'jingan-majestic-theatre'
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

    def radial(label,angle,lateral,z,material,depth):
        theta=math.radians(angle-8)
        n=[math.sin(theta),-math.cos(theta)]
        t=[math.cos(theta),math.sin(theta)]
        o=[-21.40+8*n[0]+lateral*t[0],-27.70+8*n[1]+lateral*t[1],z]
        expect(label,o,[-n[0],-n[1],0],material,depth)

    for a in (-60,-30,0,30,60):
        radial('five recessed amber-glass strips',a,.18,8.02,'amber leaded glass',2.578)
        radial('five recessed amber-glass strips',a,.19,11.45,'amber leaded glass',2.578)
    for a in (-73,-45,-15,15,45,73):
        radial('opaque pier between strips',a,.05,7.5,'cream aggregate',2.354)
    for a in (-46,0,46):
        radial('three recessed entrance leaves',a,.18,1.26,'blue grey glass',3.195)
    for a in (-63,-42,-21,0,21,42,63):
        radial('lightbox rises above recessed entrance',a,.05,4.40,'marquee opal glass',1.183)
    for x,y,h in [(-21.40,-27.70,16.95),(3.72,4.45,15.50),(25.58,20.07,16.68)]:
        expect('roof volumes',[x,y,23],[0,0,-1],'mineral roof',23-h)
    expect('street outside corner remains clear',[-23,-35,21],[0,0,-1],None)
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
