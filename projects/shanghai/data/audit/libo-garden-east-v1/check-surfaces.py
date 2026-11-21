"""Ray-test all three Libo Garden GLBs against the garden front, gables and round western return."""
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
MODEL = 'xuhui-libo-garden-east-house'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh,role):
    scene=SerialScene(mesh)
    records=[]
    def shot(label,origin,direction,material,depth,tolerance=.045):
        hit=scene.ray(origin,direction,8)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance
        records.append({'label':label,'from':origin,'direction':direction,'expected_material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})
    # The photographed five unequal-looking bays are evenly spaced along
    # the southern terrace. All five are separate apertures through the wall.
    for i in range(5):
        x=.23-4.31+2.05*i
        shot('south garden full-height opening '+str(i+1),[x+.19,-14.15,1.92],[0,1,0],'recessed grey-green glass',2.48)
    shot('plaster pier between tall south openings',[-3.06,-14.15,2.35],[0,1,0],'warm ivory roughcast',2.16)
    shot('upper terrace front coping',[.68,-14.15,4.30],[0,1,0],'pale concrete lintel and coping',2.12)
    shot('terrace roof behind low parapet',[.43,-9.92,6.10],[0,0,-1],'gravelled terrace surface',2.06)
    shot('central attic sash recessed in large gable',[.57,-7.96,8.33],[0,1,0],'recessed grey-green glass',2.37)
    shot('vertical timber on main garden gable',[-2.77,-7.96,8.46],[0,1,0],'dark red-brown exposed gable timber',1.98)
    shot('pale triangular infill beside exposed timber',[-2.42,-7.96,8.43],[0,1,0],'warm ivory roughcast',2.05)
    shot('southeast gable timber',[8.71,-12.04,8.00],[0,1,0],'dark red-brown exposed gable timber',2.32)
    shot('southeast garden casement ground glass',[8.41,-11.95,2.14],[0,1,0],'recessed grey-green glass',2.63)
    shot('southeast garden casement upper glass',[8.41,-11.95,5.90],[0,1,0],'recessed grey-green glass',2.63)
    shot('round western staircase glass',[-16.75,.48,5.63],[1,0,0],'recessed grey-green glass',3.47,.11)
    shot('inset round western support',[-16.75,.42,2.33],[1,0,0],'warm ivory roughcast',4.13,.13)
    shot('white sill projecting past round support',[-16.75,.42,4.15],[1,0,0],'warm ivory roughcast',3.38,.10)
    shot('main roof clay surface',[-4.83,4.17,12.90],[0,0,-1],'red barrel clay tiles',3.96,.08)
    shot('western chimney below vent',[-6.47,-1.45,9.83],[0,1,0],'warm ivory roughcast',1.75)
    shot('open top vent in western chimney',[-6.72,-1.45,10.25],[0,1,0],None,None)
    shot('raised southern garden step',[1.14,-12.63,2.00],[0,0,-1],'terracotta garden paving',1.76)
    shot('open lawn south of model',[.43,-15.26,6.12],[0,0,-1],None,None)
    shot('separate eastern annexe outside author geometry',[16.8,3.20,7.30],[0,0,-1],None,None)
    return {'passed':all(v['passed']for v in records),'probe_count':len(records),'probes':records}

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
