"""Check visible recesses, openings, roof steps and empty courtyards in all three GLBs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
MODEL = 'jingan-country-hospital-north-block'
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

    for x in (-1.66,.24,2.12):
        for z in (7.79,11.07,14.03,17.51):
            expect('central three-bay window stack',[x,-4,z],[0,1,0],'old glazing',2.42)
    expect('clear arch to shaded backstop',[.16,-4,1.85],[0,1,0],'entry recess',3.20)
    for x in (-15.51,-13.028,-10.4,-7.772,-5.29,5.29,7.772,10.4,13.028,15.51):
        expect('north wing lower sash',[x+.22,-4,5.67],[0,1,0],'old glazing',4.32)
    for y in (4.12,7.70,11.27):
        expect('east end hooded window',[-20,y,5.66],[1,0,0],'old glazing',2.62)
    for x,y,h in [(-12,4,17.25),(12,4,17.25),(0,6,17.25),(0,21,16.43),(0,31,16.43)]:
        expect('bar or lower clinic roof',[x,y,23],[0,0,-1],'roof surface',23-h)
    for x,y in [(-10,21),(10,21),(-10,31),(10,31),(0,34)]:
        expect('court and unbuilt southward continuation remain open',[x,y,23],[0,0,-1],None)
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
