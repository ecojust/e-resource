"""Probe the eastern horizontal bands, balcony stack, north entrance, stepped water tower, mast and surrounding streets."""
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
MODEL = 'huangpu-chung-wei-bank-building'
READER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER = PROJECT / 'vendor/meshopt_decoder.module.js'
SerialScene = runpy.run_path(str(READER))['SerialScene']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def probes(mesh):
    scene=SerialScene(mesh);records=[]
    def expect(label,origin,direction,material,depth=None,tolerance=.045):
        hit=scene.ray(origin,direction,100)
        passed=hit is None if material is None else (hit is not None and hit['material']==material and abs(hit['distance_m']-depth)<tolerance)
        records.append({'label':label,'origin_m':origin,'direction':direction,'material':material,'expected_distance_m':depth,'tolerance_m':tolerance,'first_hit':hit,'passed':passed})
    def face(label,a,b,u,z,material,depth,distance=2):
        length=math.dist(a,b);tx,ty=(b[0]-a[0])/length,(b[1]-a[1])/length;nx,ny=ty,-tx
        x,y=(a[0]+b[0])*.5+tx*u,(a[1]+b[1])*.5+ty*u
        expect(label,[x+distance*nx,y+distance*ny,z],[-nx,-ny,0],material,depth)
    east=((16.55,-32.77),(16.56,28.25));length=math.dist(*east)
    south=((-8.38,-35.43),(16.55,-32.77));sl=math.dist(*south)
    for tier in range(7):
        base=5.20+tier*3.63
        for frac in [-.235,-.135,-.035,.065,.165,.265]:
            face('six bays in eastern horizontal window band',*east,frac*length+.24,base+1.50,'recessed blue-grey glazing',2.32)
        face('pale horizontal band',*east,.018*length,base+.28,'pale grey facade facing',1.90)
        face('east red brick end bay',*east,.41*length,base+1.55,'weathered deep red facing',2)
        face('south street recessed sash',*south,.12*sl+.25,base+1.74,'recessed blue-grey glazing',2.32)
        if tier in [1,4,6]:
            face('recessed balcony-stack window',*east,-.35*length+.24,base+1.75,'recessed blue-grey glazing',2.32)
            face('projecting balcony handrail',*east,-.355*length+.23,base+.45+1.03,'dark aluminium frames',1.2875)
    a,b=(8.94,35.03),(-.88,36.52);u=math.dist(a,b)/4
    face('north bronze door surround',a,b,u,3.92,'dark bronze',2.58)
    face('north central gate glazing',a,b,u+.64,1.76,'recessed blue-grey glazing',2.45)
    for width,depth,cx,cy,z,z2,count in [(21.6,15.4,-.5,25.60,31.36,36.08,1),(16.45,12.1,-.78,26.21,36.08,41.63,2),
        (11.78,9.78,-.88,26.60,41.63,47.76,2),(7.9,7.25,-.88,26.83,47.76,51.42,1),(5.43,5.52,-.88,26.83,51.42,54.82,1),(3.06,3.30,-.88,26.83,54.82,56.79,1)]:
        for row in range(count):
            window=z+(row+.27)*(z2-z)/count
            expect('north tower step east sash',[cx+width/2+2,cy+.056,window+.40],[-1,0,0],'recessed blue-grey glazing',2.32)
    expect('flat roof behind the north tower',[2,-6,62],[0,0,-1],'weathered flat roof',30.64)
    expect('metal flagstaff near the top',[-.88+1,26.83,65.20],[-1,0,0],'galvanised mast',.9,tolerance=.055)
    for x,y in [(23,0),(0,42),(2,-42)]:
        expect('open pavement outside the building',[x,y,73],[0,0,-1],None)
    return {"passed":all(r["passed"] for r in records),"probes":records,"probe_count":len(records)}

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
