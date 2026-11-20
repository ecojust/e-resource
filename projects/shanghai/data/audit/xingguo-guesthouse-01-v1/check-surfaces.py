"""Ray-test the seven garden bays, real upper arcade, five dormers, chimneys and stairs in each delivered mesh."""
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
MODEL = 'changning-xingguo-guesthouse-01'
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

    def garden(label,x,z,material,y):
        expect(label,[x,-3,z],[0,1,0],material,None if y is None else y+3)
    for k,x in enumerate([-11.7025,-6.56,-3.28,0,3.28,6.56,11.7025]):
        front=3.03 if k in [0,6] else 3.66
        garden(f'ground-floor garden sash {k+1}',x+.23,3.14,'recessed glass',front+.32)
        garden(f'open gallery to recessed upper sash {k+1}',x+.23,8.46,'recessed glass',7.35)
    for k,x in enumerate([-6.53,-3.27,0,3.27,6.53]):
        garden(f'dormer sash {k+1}',x+.23,13.03,'recessed glass',5.55)
    for x in [-7.7,7.7]:
        garden('stone chimney stack '+str(x),x,15.62,'limestone',10.605)
    garden('open sky between the stacks',.64,15.62,None,None)
    for i in [-1,1]:
        garden('paired circular gallery shaft '+str(i),-1.64+i*.25,8.80,'carved pale stone',3.66+.17-.161)
    expect('front stone flight',[0,.78,3],[0,0,-1],'garden paving',3-.296)
    expect('grass before the steps',[0,-.6,3],[0,0,-1],None)
    expect('western arched window',[-18,5.28,3.15],[1,0,0],'recessed glass',18-14.875+.32)
    hit=scene.ray([-18,5.28,9.10],[1,0,0],42)
    records.append({'label':'west upper arcade is genuinely open','origin_m':[-18,5.28,9.10],
                    'direction':[1,0,0],'first_hit':hit,'passed':hit is None or hit['distance_m']>5})
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
