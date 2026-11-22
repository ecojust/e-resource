"""Cast rays through each arcade, upper window and roof opening on the delivered Jiujiang Road front."""
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
MODEL = 'huangpu-carlowitz-jiujiang-front'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh, role):
    scene = SerialScene(mesh)
    records = []
    def shot(label, origin, direction, reach, material, interval=None):
        hit = scene.ray(origin, direction, reach)
        ok = hit is None if material is None else (
            hit is not None and hit['material'] == material
            and interval[0] <= hit['distance_m'] <= interval[1])
        records.append(dict(feature=label, origin=origin, direction=direction, reach=reach,
                            expected_material=material, expected_depth_m=interval, hit=hit, passed=ok))

    width = 44.5552
    bay = width / 14
    west = -width / 2
    for i in range(14):
        center = west + (i + .5)*bay
        shot(f'passage to recessed shop window {i+1}', [center+.26,-3,1.08], [0,1,0], 7,
             'dark grey glazing', [5.0,5.65])
        for level,z in enumerate((6.3,10.05,13.77),2):
            shot(f'glazing at floor {level}, bay {i+1}',[center+.22,-3,z],[0,1,0],6,
                 'dark grey glazing',[3.2,3.42])
        shot(f'pierced railing {i+1}, central spindle',[center,-3,5.265],[0,1,0],3.18,
             'pale carved stone',[2.71,2.95])
        shot(f'open gap between balusters {i+1}',[center+.131,-3,5.265],[0,1,0],3.08,None)
    for i in range(1,14):
        pier = west + i*bay - .185
        shot(f'fourth floor engaged column at pier {i}',[pier,-3,14.04],[0,1,0],5,
             'pale carved stone' if i%2 else 'oxblood face brick',
             [2.79,2.915] if i%2 else [2.885,2.925])
        shot(f'paired capital under the fourth floor impost {i}',[pier,-3,14.685],[0,1,0],5,
             'pale carved stone',[2.77,2.94])
    for i in range(14):
        center=west+(i+.5)*bay
        for storey,high in enumerate((4.93+3.02,8.68+3.06,12.42+3.04),2):
            shot(f'fixed transom below fanlight, floor {storey} bay {i+1}',[center+.30,-3,high-.88],[0,1,0],5,
                 'charcoal sash',[3.14,3.27])
    for i in (12,13):
        center=west+(i+.5)*bay
        shot(f'bowed third floor east balcony {i+1}',[center,-3,9.245],[0,1,0],5,
             'pale carved stone',[2.54,2.62])
    for i,center in enumerate((west+bay,0,-west-bay),1):
        for j,offset in enumerate((-.67,.67),1):
            shot(f'gable {i}, narrow window {j}',[center+offset+.15,-3,16.85],[0,1,0],6,
                 'dark grey glazing',[3.1,3.42])
    for i,fraction in enumerate((2.9,4.9,9.1,11.1),1):
        shot(f'dormer window {i}',[west+bay*fraction+.14,-3,16.44],[0,1,0],7,
             'dark grey glazing',[4.0,4.6])
    shot('continuous open arcade behind the street piers',[west+.55,1.10,1.63],[1,0,0],width-1.10,None)
    shot('sidewalk in front of the piers',[.49,-1.89,3.28],[0,0,-1],4,None)
    shot('retained rear section beyond the delivered mesh',[.49,8.12,20],[0,0,-1],23,None)
    east=-west
    shot('continuous pale impost on the terminal brick pier',[east-.07,-3,14.91],[0,1,0],5,
         'pale carved stone',[2.72,2.88])
    shot('narrow brick rib under the east terminal impost',[east-.25,-3,13.84],[0,1,0],5,
         'oxblood face brick',[2.86,2.94])
    a=math.pi/6
    x=east+(24.87-east)*math.sin(a);y=3.5*(1-math.cos(a))
    shot('shallow pale frieze on the curve',[x,y-2,15.40],[0,1,0],4,
         'pale carved stone',[1.75,1.98])
    return {'passed':all(row['passed'] for row in records),'probe_count':len(records),'probes':records}


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
            results[role]=dict(sha256=asset['sha256'],file=path.name,**probes(decoded,role))
    report={'id':MODEL,'script_sha256':digest(Path(__file__)),'manifest_sha256':digest(args.manifest),
            'decoder_sha256':digest(DECODER),'reader_sha256':digest(READER),'results':results,
            'scope':'Checks only the sampled physical geometry in local axes; placement and viewing use independent records.'}
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
