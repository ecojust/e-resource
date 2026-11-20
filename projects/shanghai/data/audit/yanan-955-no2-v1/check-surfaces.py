"""Independently ray-test the two street-facing dormers, hipped roof and lower north return on all three delivered GLBs."""
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
MODEL = 'jingan-yanan-955-no2'
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
    # Normal rays from the street test each actual pane and plaster cheek.
    for label,x,y in [('image-right dormer',1.90,8.07),('image-left dormer',7.14,7.56)]:
        shot(label+' recessed sash glass',[x+.22,y+3.,9.62],[0,-1,0],'grey casement glass',3.32)
        shot(label+' central mullion',[x,y+3.,9.78],[0,-1,0],'weathered brown joinery',3.16)
        shot(label+' gabled plaster wall',[x+.77,y+3.,10.25],[0,-1,0],'pale yellow roughcast',3.)
        shot(label+' attic gable below the cap',[x+.26,y+3.,11.45],[0,-1,0],'pale yellow roughcast',3.)
        shot(label+' rolled roof ridge',[x,y+.05,14.],[0,0,-1],'red-brown ridge caps',1.88,.07)
    for label,x,y,h in [('north-facing main tiled plane',-3.2,6.95,9.59),('back tiled plane',-2.08,-1.12,11.33),('lower return roof',8.7,13.60,7.06)]:
        shot(label,[x,y,h+3.0],[0,0,-1],'weathered brown-red roof tiles',3.0,.16)
    shot('main long capped ridge',[0,1.77,16.04],[0,0,-1],'red-brown ridge caps',1.91,.045)
    shot('lower north return capped ridge',[8.48,11.99,10.08],[0,0,-1],'red-brown ridge caps',1.91,.045)
    shot('north return plaster wall',[9.32,17.55,3.18],[0,-1,0],'pale yellow roughcast',3.0)
    shot('north wall ground window within sill',[8.26,17.55,1.36],[0,-1,0],'grey casement glass',3.32)
    shot('upper house wall closes above the lower return',[8.13,8.98,7.18],[0,-1,0],'pale yellow roughcast',.28)
    shot('upper exposed horizontal pipe',[9.24,17.55,5.38],[0,-1,0],'dark rainwater pipe',2.92,.06)
    shot('lower exposed horizontal pipe',[9.41,17.55,4.94],[0,-1,0],'dark rainwater pipe',2.92,.06)
    course_material='weathered brown-red roof tiles' if role=='lod' else 'shadow under tile courses'
    shot('individual tile joints retained at close range',[-2.01,-1.12,14.33],[0,0,-1],course_material,3.02,.055)
    shot('north forecourt air outside return',[1.,13.4,6.6],[0,0,-1],None,None)
    shot('side path past the roof',[12.15,12.2,6.6],[0,0,-1],None,None)
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
