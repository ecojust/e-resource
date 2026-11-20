"""Check the nine arcade openings, paired steel windows, street-level rustication and upper balcony."""
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
MODEL = 'huangpu-robert-dollar-building'
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
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':bool(passed)})

    def street(label,x,z,y,material):
        expect(label,[x,-2,z],[0,1,0],material,None if y is None else y+2)

    xs=[i*5.10 for i in range(-4,5)]
    for i,x in enumerate(xs):
        street(f'ground arch {i+1}, pane',x+.19,1.05,.504,'deep glass')
        street(f'ground arch {i+1}, crown in real opening',x+.18,3.51,.504,'deep glass')
        for j,base in enumerate([5.70,9.25,12.73,16.26,19.81,23.31,26.85]):
            for sign in [-1,1]:
                off=.87 if j==6 else .91
                # The balcony rail lies in front of the lower part of row seven.
                street(f'steel sash pair {i+1}, upper tier {j+1}, side {sign:+}',x+sign*off+.13,base+1.30,.480,'recessed glass')
    for x in [-20.4,0,20.4]:
        street(f'fanlight outer decorative arch at {x:+}',x+.10,3.66,.337,'weathered iron')
    for x in [-17.85,-2.55,2.55,17.85]:
        street(f'ground pier field {x:+}',x,1.20,.054,'cut granite')
    street('projecting central balcony front edge',1.25,23.34,-.895,'light granite')
    expect('rear roof cap',[3,7,33],[0,0,-1],'roof',2.14)
    expect('Guangdong Road empty in front of model',[1,-2.6,2],[0,0,-1],None)
    expect('unmodeled western neighboring plot ground',[25,2,2],[0,0,-1],None)
    for material,minimum,height_lo,height_hi,label in [
            ('cut granite',1000,5.16,5.54,'curled stone frieze'),
            ('weathered iron',300,23.36,24.24,'balcony rail'),
            ('cut granite',50,22.14,23.13,'stone balcony brackets')]:
        tris=scene.tri[scene.mi==scene.materials.index(material)]
        hits=tris[(tris[:,:,2].min(1)>height_lo)&(tris[:,:,2].max(1)<height_hi)]
        if 'brackets' in label:hits=hits[hits[:,:,1].min(1)<-.10]
        records.append({'label':label,'triangles':len(hits),'passed':bool(len(hits)>minimum)})
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
