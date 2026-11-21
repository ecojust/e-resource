"""Check the eleven curved garden balconies, recessed outer loggias, seven front steps and single open vehicle passage in each Willow Court model."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'xuhui-willow-court'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


tests=[]
def ray(name,origin,dir,mat,length=12,depth=None):
 tests.append(dict(label=name,origin=origin,direction=dir,material=mat,maximum=length,expected_depth_m=depth))
for i in range(1,12):
 z=1.4+3.08*i
 ray(f'curved balcony {i}',[0,-11,z+.37],[0,1,0],'muted red oxide balcony',depth=2.12)
 ray(f'door in balcony {i}',[.23,-11,z+1.25],[0,1,0],'glazed dark garden door',depth=4.22)
 ray(f'east apartment window {i}',[5.14,-11,z+1.23],[0,1,0],'grey blue glass',depth=4.22)
 if i<11:
  for side in (-1,1):
   ray(f'end balcony {side} at level {i}',[side*10.03,-11,z+.44],[0,1,0],'pale yellow mineral render',depth=3.895)
   ray(f'end balcony recessed opening {side} at level {i}',[side*10.03+.23,-11,z+1.33],[0,1,0],'grey blue glass',depth=5.6)
for i in range(7):
 y=-7.10-(2.60-i*.205)+.07
 ray(f'raised step {i+1}',[0,y,1.85],[0,0,-1],'grey artificial stone steps',3,depth=1.85-(.22+i*.185))
ray('front door stone landing',[0,-8.10,1.85],[0,0,-1],'grey artificial stone steps',3,depth=.43)
for x in (8.7,10.0,11.33):
 ray('east vehicle passage '+str(x),[x,-9.2,1.87],[0,1,0],None,17.4)
 ray('ground drive soffit '+str(x),[x,2.33,2.20],[0,0,1],'pale yellow mineral render',4,depth=2.09)
ray('west recess has a rear wall',[-10.03,-9.2,1.87],[0,1,0],'pale yellow mineral render',depth=5.7)
ray('pale underside of the entrance hood',[.12,-7.76,3.21],[0,0,1],'pale yellow mineral render',2,depth=.57)
ray('projecting red entrance hood',[0,-10.0,4.02],[0,1,0],'muted red oxide balcony',4,depth=1.58)
for side in (-1,1):
 for offset in (-.62,.62):
  ray(f'basement sash under bay {side} {offset}',[side*4.91+offset+.13,-10.1,.68],[0,1,0],'grey blue glass',6,depth=3.32)
ray('main entry glass',[.19,-10.4,2.44],[0,1,0],'glazed dark garden door',depth=3.62)
for side in (-1,1):
 ray(f'ground oriel glazing {side}',[side*4.91+.23,-10.4,2.70],[0,1,0],'grey blue glass',depth=2.89)
 ray(f'open sky over lower end terrace {side}',[side*10,-2.58,36.25],[0,0,1],None,6)
ray('crown central rib',[.18,-10.4,39.65],[0,1,0],'muted red oxide balcony',depth=3.05)
ray('south garden beyond steps',[0,-10.4,2.0],[0,0,-1],None,3.)

def probes(mesh,role):
    scene=SerialScene(mesh)
    rows=[]
    for trial in tests:
        hit=scene.ray(trial['origin'],trial['direction'],trial['maximum'])
        expected=trial['material']
        passed=hit is None if expected is None else hit is not None and hit['material']==expected
        if passed and trial['expected_depth_m'] is not None:
            passed=abs(hit['distance_m']-trial['expected_depth_m']) < .035
        assert passed,(role,trial['label'],expected,hit)
        rows.append({**trial,'hit':hit,'passed':passed})
    return {'passed':True,'probe_count':len(rows),'probes':rows}

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
