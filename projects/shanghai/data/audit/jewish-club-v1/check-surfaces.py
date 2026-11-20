"""Check both five-bay galleries, double columns, circular windows, terraces, end pavilions and continuous roof in delivered assets."""
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
MODEL = 'jingan-jewish-club'
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

    def front(label,x,z,mat,d):
        expect(label,[x,-3,z],[0,1,0],mat,d)
    for side in [-1,1]:
        for x in [8.19,10.99,13.73,16.55,19.27]:
            front('five lower arcade glazed bays',side*x,1.44,'old glass',3.7)
            front('five recessed upper terrace doors',side*x,6.13,'old glass',7.8)
        front('round window beside central porch',side*4.48,3.12,'old glass',4.51)
        front('arcade stone column',side*14.95,2.10,'warm dressed stone',3.144)
        front('paired Tuscan entry column',side*2.0,1.4,'warm dressed stone',2.588)
        front('polygonal end upper sash',side*23.63,6.21,'old glass',3.24)
        front('terrace corner post',side*6.72,5.04,'balcony stone',3.15)
    front('closed panelled centre entry',.2,2.1,'panel wood',4.471)
    front('central roof dormer',.23,9.4,'old glass',4.2665)
    front('flagstaff',0,12.49,'dormer metal',6.81)
    expect('flat roof behind centre',[0,13.8,16],[0,0,-1],'grey flat roof',7.535)
    expect('branch of gallery roof',[-23.6,11.1,16],[0,0,-1],'roof red tile',5.452)
    expect('rear wall meets rear red roof at eaves',[14,18,8.54],[0,-1,0],'plain return',2.14)
    expect('left gallery gable above the lower flat roof',[-4.5,10.15,9.75],[-1,0,0],'plain return',2.05)
    expect('right gallery gable above the lower flat roof',[4.5,10.15,9.75],[1,0,0],'plain return',2.05)
    expect('clear garden between building and street',[0,-5,3],[0,0,-1],None)
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
