"""Check the photographed street section at Denis Apartments against three delivered meshes."""
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
MODEL = 'jingan-denis-apartments'
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
    coords=np.array(p['street_path_xy']); runs=[12,2,1,1,1,7]
    for segment,number in enumerate(runs):
        a,b=coords[segment:segment+2];t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]]);width=np.linalg.norm(b-a)/number
        for bay in range(number):
            mid=a+(b-a)*(bay+.5)/number
            def shoot(label,u,z,depth,wanted):
                pos=mid+t*u+n*.63
                hit(f'{segment}.{bay} {label}',(*pos,z),(*(-n),0),wanted,depth)
            shoot('recessed steel-lit window',.13,16.94,1.08,'grey green glass')
            shoot('retail glazing',.16,2.2,1.16,'shop glass')
            shoot('stone belt above second floor',.36,7.92,.68,'incised granite band')
            shoot('brick pier',width/2-.16,17.00,.83,'umber face brick')
            if segment in (1,2,3,4):shoot('raised corner attic band',.78,30.89,.74,'incised granite band')
            xy=mid-n*2.0
            hit(f'{segment}.{bay} modelled roof deck',(*xy,40.08),(0,0,-1),'weathered dark roof',2.45)
            xy=mid+n*1.8
            hit(f'{segment}.{bay} clear sidewalk',(*xy,1.),(0,0,-1),None,1.3)
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
