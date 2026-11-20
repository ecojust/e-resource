"""Measure the arched street entrance, lawn windows and two-storey veranda."""
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
MODEL = 'jingan-huashan-american-school-office'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh, role):
    scene=SerialScene(mesh);records=[]
    def expect(label,origin,direction,material,depth=None,tolerance=.045):
        hit=scene.ray(origin,direction,100)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance)
        records.append({'label':label,'origin_m':origin,'direction':direction,'material':material,'expected_distance_m':depth,'tolerance_m':tolerance,'first_hit':hit,'passed':passed})
    def side(label,x,y,z,face,mat,dist,tol=.045):
        expect(label,[x,y,z],[0,1 if face=='north' else -1,0],mat,dist,tol)
    wall='warm off-white plaster'; glass='blue-grey recessed glazing'; trim='pale stone trim'
    for x in [-11.90,-8.49,-5.16,5.16,8.49,11.90]:
        for z in [1.70,5.43]:
            side('street classroom recessed pane',x+.20,-8.0,z,'north',glass,2.32)
        # The detailed five-row sash has a transom exactly at 5.25 m.
        # The three-row distant sash leaves this point in a glazed pane.
        if role=='lod':
            side('distant upper sash pane',x+.20,-8.0,5.25,'north',glass,2.32)
        else:
            side('upper timber transom',x+.20,-8.0,5.25,'north','cream painted sash',2.16)
    side('arched portal coping',.05,-11.05,3.66,'north',trim,1.91)
    side('inset entrance glass',.44,-11.05,2.12,'north',glass,4.79)
    side('entrance timber at threshold',.27,-11.05,.77,'north','dark timber entrance',4.81)
    side('solid roadside porch pier',2.02,-11.05,2.31,'north',wall,2.0)
    side('porch attic vent',.52,-11.05,5.19,'north','dark metal flashings',1.985)
    for x in [-4.70,.10,4.90,9.68,13.44]:
        for z in [1.76,6.49]:
            side('two-storey garden veranda pier',x+.04,9,z,'south',wall,1.56)
    for u in [-11.70,-7.20,-2.55,2.40,7.12,11.70]:
        for z in [1.63,6.30]:
            x=-u+.20
            side('garden door or window behind open bay',x,8.70,z,'south',glass,5.22)
    side('gallery handrail',2.82,8.70,5.28,'south','slender black iron rail',1.26,tol=.04)
    theta=math.pi/4
    cx,cy=-9.7-5*math.cos(theta),3.35+4.05*math.sin(theta)
    side('curved eastern veranda pier',cx,cy+1,2.06,'south',wall,.73)
    for x in [-12.4,0,12.4]:
        expect('terracotta garden gallery floor',[x,5.73,.87],[0,0,-1],'terracotta gallery paving',.56)
    for x,y in [(0,10.25),(19,0),(-20,0),(-9,-12.07)]:
        expect('garden or path outside the walls',[x,y,18],[0,0,-1],None)
    return {'passed':all(r['passed']for r in records),'probes':records,'probe_count':len(records)}

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
