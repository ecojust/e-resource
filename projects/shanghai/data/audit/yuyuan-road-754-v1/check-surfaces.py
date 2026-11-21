"""Test physical sections, the actual arched openings, pierced rails and lane gates at 754 Yuyuan Road."""
import argparse
import numpy as np
import math
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'changning-yuyuan-road-754'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);results=[]
    p=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    def hit(name,origin,direction,wanted,limit=5):
        origin=list(map(float,origin));direction=list(map(float,direction))
        first=scene.ray(np.array(origin),np.array(direction),limit)
        allowed=[wanted] if isinstance(wanted,str)else wanted
        ok=first is None if allowed is None else bool(first and first['material'] in allowed)
        results.append({'name':name,'origin_author_m':origin,'direction':direction,'expected_first_material':allowed,'first_hit':first,'passed':ok})
    stucco=['blue grey stucco','incised mortar']
    for x in [-1.93,-1.55,-1.13,-.82,.83,1.12,1.54,1.89]:
        for h in [2.98,3.59,4.09]:
            hit(f'low front patterned plaster {x} {h}',(x,-.33,h),(0,1,0),stucco,.60)
    for side in [-1,1]:
        for y in [1.14,2.80,4.13]:
            hit(f'low room return {side} {y}',(side*2.43,y,3.58),(-side,0,0),stucco,.50)
    for x in [-.41,-.24,.21,.43]:
        hit(f'arched glazing {x}',(x,-.026,2.75),(0,1,0),'arch glazing',.23)
    hit('central curved head masonry',(0,-.32,3.57),(0,1,0),stucco,.50)
    hit('square vent in deep reveal',(0,-.03,4.55),(0,1,0),'dark vent',.30)
    hit('vent projecting plaster surround',(.345,-.31,4.60),(0,1,0),'pale cement',.36)
    for z in [1.5,1.75,2.08,2.30]:
        hit(f'iron grille centre bar {z}',(0,-.38,z),(0,1,0),'ivory iron',.28)
    for k,(cx,h) in enumerate([(-1.92,6.39),(-.58,6.79),(.92,6.62)]):
        hit('upper arc glass '+str(k),(cx-1.84+.105,11.20,h-.275),(0,1,0),'arch glazing',.60)
    for k,y in enumerate([10.21,10.72,11.28,11.84,12.44,13.11,13.66]):
        hit('balcony floor '+str(k),(2.35,y,4.46),(0,0,-1),'pale cement',.54)
    for k in range(12):
        y=10.10+(k+.5)*3.88/12
        hit('balcony open aperture '+str(k),(3.09,y,4.67),(-1,0,0),None,.37)
        hit('balcony stone rail cap '+str(k),(2.92,y,5.34),(0,0,-1),'cut coping',.42)
    for k,(x,y)in enumerate([(-4.48,-1.61),(-2.28,-1.38),(1.39,-1.48),(3.62,-1.02)]):
        hit('green gate pier cap '+str(k),(x,y,3.09),(0,0,-1),'green barrel tile',.55)
    for x,y,z in [(0,2,4.90),(-2.9,7,5.72),(-2.1,13.2,8.29)]:
        hit('estimated flat roof deck '+str(x),(x,y,z+.51),(0,0,-1),'roof deck',1.05)
    for x,y in [(0,-.65),(3.02,3.25),(-3.01,-2.06)]:
        hit('open lane or forecourt '+str(x),(x,y,.75),(0,0,-1),None,1.0)
    return {'triangles':len(scene.tri),'probes':results,'passed':sum(r['passed'] for r in results)}


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
    assert all(r['passed']==len(r['probes']) and r['triangles']==manifest['assets'][role]['triangles'] for role,r in results.items())
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    for role,test in results.items():
        print(role,'passed' if test['passed'] else [r for r in test['probes'] if not r['passed']])
    return all(r['passed'] for r in results.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
