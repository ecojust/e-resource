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
MODEL = 'xuhui-guo-dihuo-west-house'
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
    # Local coordinates are metres. The close camera faces the photograph's
    # curved bay from outside the paved garden terrace.
    shot('lower curved garden glass',[1.35,-9.65,2.32],[0,1,0],'smoked garden window glass',2.91,.09)
    shot('centre mullion on curved bay',[1.,-9.65,2.27],[0,1,0],'charcoal steel window frames',2.84,.045)
    shot('upper transom of curved window',[1.39,-9.65,3.06],[0,1,0],'charcoal steel window frames',2.86,.11)
    shot('plastered curved sill',[1.25,-9.65,1.02],[0,1,0],'pale warm-grey roughcast',2.90,.07)
    shot('upper curved window head',[1.34,-9.65,4.12],[0,1,0],'pale warm-grey roughcast',2.92,.09)
    shot('arched front under balcony',[1.32,-7.25,3.16],[0,0,1],'light painted concrete soffit',1.14)
    shot('raised balcony fascia',[-1.65,-10.01,5.06],[0,1,0],'pale warm-grey roughcast',2.01,.055)
    shot('outer deck slab front',[-1.65,-10.01,4.48],[0,1,0],'light painted concrete soffit',2.01,.055)
    shot('metal rail above the parapet',[-1.65,-10.01,5.87],[0,1,0],'garden balustrade dark metal',1.97,.06)
    shot('open air above balcony coping',[-1.17,-8.27,5.74],[0,0,1],None,None)
    shot('top of tongue-shaped rain canopy',[.55,-6.48,10.13],[0,0,-1],'light painted concrete soffit',2.21)
    shot('underside of canopy',[.55,-6.43,6.42],[0,0,1],'light painted concrete soffit',1.31)
    shot('east thin canopy support',[2.24,-7.25,6.74],[0,1,0],'charcoal steel window frames',1.51,.06)
    shot('lower east loggia column',[6.29,-8.08,2.70],[0,1,0],'charcoal steel window frames',1.97,.055)
    shot('roof deck material',[-6.20,2.10,12.15],[0,0,-1],'weathered grey roof finish',3.49)
    shot('upper stair flat cap',[.42,6.28,12.15],[0,0,-1],'weathered grey roof finish',2.81)
    shot('north central stair glazing',[.54,9.62,6.25],[0,-1,0],'pale stairwell glazing',2.41,.055)
    shot('north bay cap outer edge',[1.40,9.63,8.90],[0,-1,0],'pale warm-grey roughcast',2.10,.055)
    shot('front terrace under approach',[1.37,-7.67,2.06],[0,0,-1],'grey terrazzo and plinth',1.52,.06)
    shot('unenclosed garden south of steps',[.58,-10.10,5.50],[0,0,-1],None,None)
    shot('open strip towards east villa',[14.2,1.16,5.62],[0,0,-1],None,None)
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
