"""Probe the three finished meshes for five bowed arches, recessed five-bay galleries, working forecourt and separate northeast ballroom."""
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
MODEL = 'huangpu-french-club'
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

    front=-23.91;glass='smoky green glazing';pale='pale cut cornice';stone='cream limestone'
    for name,lo,hi in [('west',-32.33,-10.71),('east',16.31,39.73)]:
        width=hi-lo;step=width/5
        for j in range(5):
            x=lo+(j+.5)*step+.22
            expect(name+' segmental ground-floor opening '+str(j+1),[x,front-2,1.44],[0,1,0],glass,2.32)
            expect(name+' deeply recessed upper door '+str(j+1),[x,front-2,7.77],[0,1,0],glass,3.99)
            expect(name+' octagonal transom '+str(j+1),[x,front-2,10.68],[0,1,0],'dark bronze sash',3.88)
        expect(name+' upper portico column',[lo+step,front-2,8.49],[0,1,0],stone,1.61)
    def bow(t):return (2.80+13.51*math.sin(t),front-4.80*math.cos(t))
    for j in range(5):
        a=bow(-math.pi/2+math.pi*j/5);b=bow(-math.pi/2+math.pi*(j+1)/5)
        dx=b[0]-a[0];dy=b[1]-a[1];ll=math.hypot(dx,dy);nx,ny=dy/ll,-dx/ll
        x=(a[0]+b[0])*.5+dx/ll*.26;y=(a[1]+b[1])*.5+dy/ll*.26
        expect('bowed salon arch '+str(j+1),[x+2*nx,y+2*ny,8.08],[-nx,-ny,0],glass,2.32)
    for name,x in [('west end',(-39.65-32.33)/2),('east end',(39.73+47.46)/2)]:
        expect(name+' tall arch',[x+.26,front-2,8.10],[0,1,0],glass,2.32)
    expect('large green roof over northeastern ballroom',[30.51,14.0,21],[0,0,-1],'green ballroom metal roof',6.50)
    expect('main low roof',[9.11,-8.6,21],[0,0,-1],'warm grey roof',8.32)
    expect('garden approach outside entrance canopy',[1.45,-36,20],[0,0,-1],None)
    expect('separate 34-floor tower footprint excluded',[-19.5,25.5,25],[0,0,-1],None)
    expect('low canopy over garden arrival',[6.74,-30.06,15],[0,0,-1],'glazed entrance canopy',9.87)
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
