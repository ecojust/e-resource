"""Probe the door, classroom windows, five dormers, belfry and paths of the school."""
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
MODEL = 'xuhui-shanghai-american-school-main'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);records=[]
    def expect(label,origin,direction,material,depth=None,tolerance=.045):
        hit=scene.ray(origin,direction,100)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance)
        records.append({'label':label,'origin_m':origin,'direction':direction,'material':material,'expected_distance_m':depth,'tolerance_m':tolerance,'first_hit':hit,'passed':passed})
    glass='cool recessed glazing'
    brick='weathered red facing brick'
    stone='warm light limestone'
    ivory='painted ivory sash and tower'
    for x in [-10.25,-7.03,-4.10,0,4.10,7.03,10.25]:
        expect('central upper sash',[x+.21,-10.92,6.04],[0,1,0],glass,2.32)
        if x:
            expect('central ground sash',[x+.21,-10.92,1.38],[0,1,0],glass,2.32)
    expect('door timber leaf',[.28,-10.92,2.14],[0,1,0],'dark timber door',2.32)
    expect('doorway carved crest',[0,-10.92,4.50],[0,1,0],stone,1.74)
    expect('portal stone pilaster',[1.47,-10.92,2.15],[0,1,0],stone,1.675)
    expect('brick face between the bays',[8.65,-10.92,6.35],[0,1,0],brick,2)
    for side in [-1,1]:
        for i in [-9.39,-6.30,-3.16,0,3.16,6.30,9.39]:
            x=side*24.95+i
            for z in [1.40,6.13]:
                expect('classroom wing recessed sash',[x+.22,-10.25,z],[0,1,0],glass,2.32)
    for x in [-9.80,-4.92,0,4.92,9.80]:
        expect('arched central dormer sash',[x+.21,-10.42,11.08],[0,1,0],glass,2.32)
        expect('arched central dormer side face',[x+.93,-10.42,11.10],[0,1,0],ivory,2)
    for x in [-26.78,26.78]:
        expect('wide flanking pediment sash',[x+.19,-9.75,10.48],[0,1,0],glass,2.32)
    expect('tower base meets the pitched roof',[.38,-3.80,14.53],[0,1,0],ivory,2.15)
    expect('square tower body',[.20,-3.8,16.1],[0,1,0],ivory,2.11)
    expect('arched belfry sash',[.13,-3.50,18.54],[0,1,0],glass,2.52,tolerance=.05)
    for x in [-1.43,1.43]:
        expect('urn on front edge of the tower base',[x,-3.40,18.15],[0,1,0],stone,1.67,tolerance=.06)
    expect('separate pyramidal roof hood',[4.65+.08,1.87,25],[0,0,-1],stone,7.35,tolerance=.07)
    for x,y in [(-42,0),(0,-14),(0,19),(31,45)]:
        expect('unbuilt path or surviving building outside the model',[x,y,26],[0,0,-1],None)
    return {'passed':all(r['passed'] for r in records),'probes':records,'probe_count':len(records)}

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
