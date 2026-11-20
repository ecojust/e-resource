"""Probe the three finished meshes for the bronze doors, two shafts, three window stacks, two cantilever balconies, the roof and independently open streets."""
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
MODEL = 'huangpu-yokohama-specie-bank'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh)
    records=[]

    def expect(label,origin,direction,material,depth=None,tolerance=.04):
        hit=scene.ray(origin,direction,80)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance)
        records.append({'label':label,'origin_m':origin,'direction':direction,'material':material,'expected_distance_m':depth,
                        'tolerance_m':tolerance,'first_hit':hit,'passed':passed})

    def face(label,u,z,material,depth,x=39.07,tolerance=.04):
        expect(label,[x+2,-5.405+u,z],[-1,0,0],material,depth,tolerance)

    for u in [-4.68,0,4.68]:
        face('paired bronze entrance leaves',u+.33,2.74,'patinated bronze',2.4055)
        face('recessed entrance upper transom',u,6.52,'patinated bronze',2.395)
        for bottom in [9.94,14.02,18.23,22.49]:
            face('four-storey central window group',u+.29,bottom+.50,'inset cool grey glass',2.32)
        for z in [13.08,17.26,21.46]:
            face('dark spandrel panel',u+.54,z,'dark bronze spandrels',1.945)
    for u in [-2.34,2.34]:
        face('full round Ionic shaft',u,16.5,'warm granite shafts',1.005)
        face('Ionic capital abacus',u,25.27,'pale carved granite',1.015)
    for u in [-9.64,9.64]:
        face('flanking ground window',u+.27,2.65,'inset cool grey glass',2.32)
        face('cantilever balcony slab',u,9.38,'pale carved granite',1.17)
        face('balcony handrail',u,10.48,'blackened metalwork',1.095)
        face('balcony sash horizontal rail',u+.29,11.72,'blackened metalwork',2.16)
        face('sash pane behind balcony canopy',u+.29,11.22,'inset cool grey glass',2.32)
    for u in [-9.95,-5.05,0,5.05,9.95]:
        expect('recessed sixth-floor sash',[39.55,-5.40+u+.30,31.08],[-1,0,0],'inset cool grey glass',2.32)
    face('vermilion ICBC roundel',-2.92+.755,27.00,'vermilion enamel',1.868)
    expect('central stepped roof crest',[37.55+2.,-5.40,35.35],[-1,0,0],'pale carved granite',1.91)
    expect('flat grey upper roof',[30,0,39],[0,0,-1],'flat grey roof',5.18)
    expect('west rear roof light',[-15.8,10.6,34],[0,0,-1],'inset cool grey glass',5.14)
    expect('street in front of the three doors',[42,-5,40],[0,0,-1],None)
    expect('open notch beside separate north property',[19,17,40],[0,0,-1],None)
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
