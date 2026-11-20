"""Check the two gate leaves, enamel number plate, stone caps and actual apertures on all three delivered meshes."""
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
MODEL = 'jingan-villa-no25'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh,role):
    scene=SerialScene(mesh)
    records=[]
    def ray(label,x,z,expected,depth=2.0,tol=.045):
        hit=scene.ray([x,-2,z],[0,1,0],8)
        allowed=[expected] if isinstance(expected,str) else expected
        passed=hit is None if allowed is None else hit is not None and hit['material'] in allowed and abs(hit['distance_m']-depth)<tol
        records.append(dict(label=label,x=x,z=z,expected=allowed,depth_m=depth,first_hit=hit,passed=passed))
    brick=['burnt sienna facing brick','red-brown alternate facing brick','dark fired header brick','warm grey brick joints']
    iron='black gate and grille iron'
    ray('green enamel plate beside the opening',-1.643,2.265,'enamel-green street plate',1.965)
    ray('garden wall left of the gate',-2.18,1.03,brick)
    ray('garden wall right of the gate',1.77,.83,brick)
    ray('left pier masonry',-1.59,1.5,brick)
    ray('right pier masonry',.29,1.54,brick)
    ray('left granite plinth',-1.59,.19,'bush-hammered granite plinth',1.97)
    ray('right granite plinth',.31,.19,'bush-hammered granite plinth',1.97)
    ray('right plaster shoulder',.304,2.64,'grey rendered pier dressings',1.96)
    ray('right upper cap',.295,2.963,'weathered grey projecting caps',1.92)
    ray('opening split between iron leaves',-.64,.78,None)
    ray('closed left gate leaf',-.99,.82,['charcoal leaf panels',iron],1.96,.055)
    ray('closed right gate leaf',-.25,.84,['charcoal leaf panels',iron],1.96,.055)
    ray('left centre rail',-1.01,1.055,iron,1.92,.04)
    ray('right upper rail',-.24,2.055,iron,1.92,.04)
    ray('pale rectangular head',-.60,2.732,'off-white painted transom surround',1.99)
    ray('coping above the gate opening',-.61,2.919,'weathered grey projecting caps',1.965)
    ray('bar in the transom above the leaves',-1.277,2.385,iron,2.051)
    ray('sky visible between transom bars',-1.243,2.385,None)
    ray('open horizontal wall vent',.728,1.748,None)
    ray('outside disjoint neighbor wall',2.67,1.33,None)
    ray('air over projecting caps',-.65,3.105,None)
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
