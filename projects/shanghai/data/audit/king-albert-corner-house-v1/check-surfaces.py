"""Independently ray-test the paired bays, balcony, street gable and chimney on all three delivered GLBs."""
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
MODEL = 'huangpu-king-albert-corner-house'
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
    def outward(label,a,b,along,z,material,depth):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);tx,ty=dx/length,dy/length;nx,ny=ty,-tx
        shot(label,[(a[0]+b[0])/2+along*tx+3*nx,(a[1]+b[1])/2+along*ty+3*ny,z],[-nx,-ny,0],material,depth)
    west=((-7.62,-8.53),(-5.57,-8.74));east=((5.57,-8.74),(7.62,-8.53));middle=((-2.90,-6.15),(2.90,-6.15))
    for k,z in enumerate((0.,3.12,6.24,9.36)):
        for name,edge in [('west',west),('east',east)]:
            outward(name+' octagonal room window '+str(k+1),*edge,.18,z+1.22,'muted blue-grey window glass',3.32)
            outward(name+' plaster spandrel '+str(k+1),*edge,.11,z+.58,'warm pale-yellow roughcast',3.00)
    outward('ground-floor center door',*middle,.24,1.22,'painted front doors',3.32)
    outward('Brick between central door and side window',*middle,1.07,1.8,'russet facing brick',3.)
    outward('street balcony metal handrail',*middle,.58,4.13,'black balcony iron',2.3575)
    outward('street balcony solid front',*middle,.34,6.64,'warm pale-yellow roughcast',2.335)
    outward('bright triangular gable',*middle,.91,13.18,'warm pale-yellow roughcast',2.97)
    outward('gable attic vent glazing',*middle,.20,13.02,'muted blue-grey window glass',3.32)
    shot('western chimney cap',[-8.17,-.73,17.50],[0,0,-1],'ochre plaster parapet moulding',1.905)
    shot('west chimney head shadow',[-8.00,-3.60,15.30],[0,1,0],'dark chimney opening',2.37)
    shot('east rear chimney cap',[7.19,2.29,17.0],[0,0,-1],'ochre plaster parapet moulding',1.925)
    shot('air in northern rear wing recess',[0,6.0,9.70],[0,0,-1],None,None)
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
