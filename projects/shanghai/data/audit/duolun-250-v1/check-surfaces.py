"""Probe the three finished meshes for the curved portal, lobby, arcades and unbuilt rounded corner."""
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
MODEL = 'hongkou-duolun-250'
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

    ca=math.cos(math.radians(135));sa=math.sin(math.radians(135))
    def native(x,y,z):
        return [x*ca-y*sa,x*sa+y*ca,z]
    radius=12.34;side=radius*math.pi/4;cx=4.03;cy=-2.05
    def outward(label,s,z,material,distance):
        angle=math.radians(135)+max(-side,min(side,s))/radius
        nx,ny=math.cos(angle),math.sin(angle)
        x=cx+radius*nx;y=cy+radius*ny
        if s< -side:x+=-side-s
        if s>side:y-=s-side
        expect(label,native(x+nx*2,y+ny*2,z),native(-nx,-ny,0),material,distance)
    outward('central recessed entrance',.20,1.20,'dark entrance timber',2.31)
    for u in [-1.30,1.30]:
        outward('narrow lower companion opening',u+.17,2.15,'smoked window glass',2.31)
    for u in [-1.3,0,1.3]:
        outward('three upper horseshoe openings',u+.15,6.22,'smoked window glass',2.31)
    for side_sign in [-1,1]:
        off=side_sign*5.04
        outward('single lower horseshoe',off+.18,2.24,'smoked window glass',2.31)
        for j in [-.55,.55]:
            outward('twin upper windows',off+j+.13,5.97,'smoked window glass',2.31)
        for j in [-1,0,1]:
            outward('three lower flank openings',side_sign*10.35+j*1.4+.19,2.23,'smoked window glass',2.31)
        for j in [-2,-1,0,1,2]:
            outward('five upper flank openings',side_sign*10.35+j*.91+.13,5.93,'smoked window glass',2.31)
    for u in [-1.96,-.76,.76,1.96]:
        outward('central portal freestanding column',u,2.08,'warm carved stone',1.66)
    outward('central parapet',.32,8.82,'pale grey dressed stone',2.057)
    expect('flat roof away from parapet',native(3,-4,13),[0,0,-1],'grey flat roof',4.74)
    expect('rounded corner opens onto the outside pavement',native(-7.9,9.4,12),[0,0,-1],None)
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
