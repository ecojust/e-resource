"""Probe the three finished meshes for the Ionic corner portal, independent fanlight, both rows of upper sash, twelve street arches and the stepped roof."""
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
MODEL = 'huangpu-yongnian-life-insurance-building'
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
    portal=((21.14,10.02),(17.94,13.13))
    def front(label,u,z,mat,depth):face(label,*portal,u,z,mat,depth)
    front('recessed rectangular door behind grille',.23,2.13,'door grille',2.92)
    front('portal fanlight inside the flat lintel',.17,4.18,'blue black glazing',2.65)
    front('dark granite lower portal shaft',1.80,2.74,'polished red granite',1.62)
    front('upper colossal corner shaft',1.72,10.73,'polished red granite',1.605)
    front('carved lintel',.14,5.85,'pale brown granite trim',1.62)
    front('lower corner casement',.25,8.07,'blue black glazing',2.32)
    front('upper corner casement',.25,13.82,'blue black glazing',2.32)
    for name,edge,count in [('Sichuan',((21.14,-13.03),(21.72,8.68)),5),
                            ('Guangdong',((16.87,13.44),(-19.31,13.39)),7)]:
        a,end=edge;length=math.dist(a,end);width=length/count
        for i in range(count):
            center=(i+.5)*width-length/2
            for z,line in [(2.82,'street arch'),(8.44,'middle sash'),(13.35,'top sash')]:
                face(name+' '+line+' '+str(i+1),a,end,center+.24,z,'blue black glazing',2.32)
        face(name+' Ionic shaft',a,end,-length/2+width,9.08,'polished red granite',1.54)
    expect('main flat street-wing roof',[11.0,4.0,22],[0,0,-1],'weathered roof',5.86)
    expect('local fourth-storey roof',[1.1,1.8,22],[0,0,-1],'weathered roof',3.11)
    expect('open northeastern intersection',[23.0,15.0,22],[0,0,-1],None)
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
