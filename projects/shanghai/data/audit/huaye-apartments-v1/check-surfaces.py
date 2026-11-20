"""Check actual material and depth at apartment windows, balconies, arcades, tower and court voids."""
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
MODEL = 'jingan-huaye-apartments'
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

    # Local Y grows into the house from the photographed southwest court.
    for cx in (-10.60,10.60):
        for z in (8.99,15.69,22.39):
            expect('west court wide sash',[cx+.43,-15,z],[0,1,0],'cool glazing',3.75)
            expect('narrow flanking sash',[cx+5.23,-15,z],[0,1,0],'cool glazing',3.75)
        expect('solid pier beside broad bay',[cx+3.87,-15,10.13],[0,1,0],'ivory stucco',3.45)
        expect('east garden broad sash',[cx-.44,15,15.69],[0,-1,0],'cool glazing',2.95)
        expect('west upper loggia arch',[cx+.22,-12,28.37],[0,1,0],'cool glazing',5.60)
        expect('east upper loggia arch',[cx+.22,13,28.36],[0,-1,0],'cool glazing',4.60)
    for z in (5.02,8.36,11.71,15.06,18.41,21.76,25.11):
        expect('stacked rounded parapet',[.12,-13,z],[0,1,0],'ivory stucco',4.02)
    for x in (-1.61,.16,1.91):
        expect('tower upper arched row',[x,-12,35.04],[0,1,0],'cool glazing',6.12)
        expect('tower lower row',[x,-12,32.27],[0,1,0],'cool glazing',6.12)
    expect('entry canopy at garden',[.42,7.60,8],[0,0,-1],'ochre stone',4.71)
    for x,y in [(0,-12),(0,12),(-22,0),(19,0)]:
        expect('open exterior courts and setbacks',[x,y,20],[0,0,-1],None)
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
