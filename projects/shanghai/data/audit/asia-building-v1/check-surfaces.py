"""Query each finished mesh for both street fronts, paired colonnades, recessed balconies, roof and clear street."""
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
MODEL = 'huangpu-asia-building'
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
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':passed})

    angle=math.atan2(11.732,37.743)
    ca,sa=math.cos(angle),math.sin(angle)
    def enu(x,y,z):
        return [x*ca-y*sa,x*sa+y*ca,z]
    def facade(label,a,b,u,z,material,depth):
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy);tx,ty=dx/length,dy/length;nx,ny=ty,-tx
        x=(a[0]+b[0])/2+tx*u+nx*3
        y=(a[1]+b[1])/2+ty*u+ny*3
        expect(label,enu(x,y,z),enu(-nx,-ny,0),material,depth)
    for name,a,b in [('south',(-19.25,-19.72),(15.67,-19.72)),('east',(19.34,-16.05),(19.34,19.37))]:
        for u in [-4.71,0,4.71]:
            for z in [12.10,16.30,20.36,24.61,28.81]:
                facade(name+' deep loggia rear glazing',a,b,u+.38,z,'smoky blue glazing',5.73)
        for u in [-2.92,-2.23,2.23,2.92]:
            facade(name+' street portal column',a,b,u,6.90,'carved warm limestone',2.18)
        for u in [-6.99,-2.76,-1.98,1.98,2.76,6.99]:
            facade(name+' upper colonnade',a,b,u,25.58,'carved warm limestone',2.98)
        facade(name+' inset entrance',a,b,.35,1.48,'dark timber',3.35)
        length=math.dist(a,b)
        flank=7.05+(length/2-7.05)*.29
        facade(name+' flanking sash',a,b,flank+.33,15.71,'smoky blue glazing',3.35)
    facade('splayed corner recessed sash',(16.42,-18.53),(18.15,-16.80),.26,15.68,'smoky blue glazing',3.35)
    for x,y in [(-3.0,-2.30),(3.2,4.29)]:
        expect('glazed central roof',enu(x,y,40),[0,0,-1],'green roof glass',9.12)
    expect('flat southwest attic pavilion roof',enu(-14,-14,40),[0,0,-1],'weathered roof',5.87)
    expect('street remains open at the southeast corner',enu(22,-22,17),[0,0,-1],None)
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
