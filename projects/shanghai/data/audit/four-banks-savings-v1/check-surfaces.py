"""Probe the three finished meshes for the arched bank entrance, radial fanlight, glazing, four-lobed tower crown and street terraces."""
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
MODEL = 'huangpu-four-banks-savings-building'
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

    def face(label,start,end,u,z,material,depth):
        dx,dy=end[0]-start[0],end[1]-start[1];length=math.hypot(dx,dy);tx,ty=dx/length,dy/length
        nx,ny=ty,-tx
        x=(start[0]+end[0])/2+u*tx;y=(start[1]+end[1])/2+u*ty
        expect(label,[x+2*nx,y+2*ny,z],[-nx,-ny,0],material,depth)
    portal=((2.70,-18.04),(6.45,-15.62));front=lambda label,u,z,mat,depth:face(label,*portal,u,z,mat,depth)
    front('door recessed behind grille',.12,2.31,'shadowed entrance doors',3.02)
    front('radial bronze fanlight rib',0,9.48,'dark bronze grille',2.13)
    front('radial fanlight dark glass',.67,9.48,'recessed green glass',2.39)
    front('solid marble doorway surround',1.99,7.9,'warm white marble',1.78)
    for level in range(4):
        front('red-brick tower window '+str(level+1),.27,14.88+4.48*level,'recessed green glass',2.32)
        front('dark fired-brick spandrel '+str(level+1),1.24,16.94+4.48*level,'dark Taishan face brick',2.0)
    front('pale tower square window', .16,32.62,'recessed green glass',2.32)
    front('pale tower arched window',.27,37.48,'recessed green glass',2.32)
    front('dark quatrefoil opening',.18,44.18,'dark bronze grille',2.32)
    front('solid crown adjacent to quatrefoil',1.56,44.2,'warm white marble',2.0)
    for name,edge,count in [('Hankou',((-7.90,-18.77),(.25,-18.81)),2),('Sichuan',((8.54,-13.06),(8.22,17.77)),6)]:
        a,c=edge;length=math.dist(a,c)
        for i in range(count):
            u=(i+.5)*length/count-length/2+.28
            face(name+' recessed pale upper arch '+str(i+1),a,c,u,32.87,'recessed green glass',2.32)
            face(name+' dark-brick storey window '+str(i+1),a,c,u,15.13,'recessed green glass',2.32)
    expect('setback roof',[-3.9,5,55],[0,0,-1],'weathered roof',14.72)
    expect('tower roof',[3.15,-14.25,55],[0,0,-1],'weathered roof',8.37)
    expect('open intersection outside the entrance',[12,-20,20],[0,0,-1],None)
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
