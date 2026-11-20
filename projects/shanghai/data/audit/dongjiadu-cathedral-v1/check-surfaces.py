"""Probe the three doors, louvers, robed niches, inscriptions and cross in each shipped GLB."""
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
MODEL = 'huangpu-dongjiadu-cathedral'
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

    def front(label,x,z,mat,distance):
        expect(label,[x,-4,z],[0,1,0],mat,distance)
    for s in [-1,1]:
        front('side entrance wood',s*8.74,1.65,'wood leaf',4.37)
        front('side upper sash',s*8.59,6.19,'upper glass',4.32)
        front('tower louvre slat',s*13.52,12.70,'stone slat',4.102)
        front('gap behind louvre slats',s*13.52,12.85,'louvre shadow',4.28)
        front('figure in outer blind niche',s*13.55,2.62,'cream carving',3.929)
        front('bell tower compound cap',s*13.52,18.36,'cap metal',3.987)
        front('swept scroll relief',s*6.61,14.2,'warm stone',3.835)
    front('central door',.1,5.,'wood leaf',4.37)
    front('shaped fanlight',.47,7.64,'upper glass',4.32)
    front('clock tile field',1.65,15.32,'red ochre',3.865)
    front('central gilded boss',.1,15.32,'clock gilt',3.642)
    front('dark circular dial',.80,15.50,'clock face',3.685)
    for x,z in [(-4.30,8.98),(-4.37,2.54),(4.41,8.90),(4.44,2.62)]:
        front('upper/lower inscription stroke',x,z,'inscription ink',3.762)
    for z in [22.19,21.30,20.365]:
        front('vertical top title stroke',0,z,'inscription ink',3.774)
    front('iron rail above crest',.09,24.55,'inscription ink',3.8)
    expect('clear forecourt',[0,-3,5],[0,0,-1],None)
    expect('outside west return',[-16.,1.5,4],[0,0,-1],None)
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
