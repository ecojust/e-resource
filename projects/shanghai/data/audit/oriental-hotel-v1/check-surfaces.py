"""Check the three Ionic orders, balconies, dated crown, repaired doorway and two streets on every delivered mesh."""
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
MODEL = 'huangpu-oriental-hotel'
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

    p=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    r=np.array(p['study_uv_m'])
    def face_probe(label,a,b,x,z,mat,depth):
        v=b-a;v=v/np.linalg.norm(v);n=np.array([v[1],-v[0]])
        start=(a+b)/2+v*x+n*5
        expect(label,[float(start[0]),float(start[1]),z],[-float(n[0]),-float(n[1]),0],mat,depth)
    for label,ai,bi in [('western entrance',0,1),('Guangdong chamfer',1,2),('Beihai chamfer',5,0)]:
        a,b=r[ai],r[bi];length=np.linalg.norm(b-a)
        for sign in [-1,1]:
            face_probe(label+' Ionic shaft '+str(sign),a,b,sign*length*.282,14,'carved pale stone',4.25)
        for z in [10.84,15.12,19.54]:
            face_probe(label+' recessed balcony door '+str(z),a,b,.20,z,'recessed glass',5.32)
        face_probe(label+' upper sash horizontal transom',a,b,.20,19.31,'bronze window frame',5.16)
        for z in [13.30,17.61]:
            face_probe(label+' projecting balcony '+str(z),a,b,.22,z,'carved pale stone',4.105)
        for z in [24.58,27.62]:
            face_probe(label+' upper gallery sash '+str(z),a,b,.22,z,'recessed glass',5.32)
        if ai==0:
            face_probe(label+' recent rectangular street doorway',a,b,.31,2.13,'recessed glass',5.32)
        else:
            face_probe(label+' street-level arched glazing',a,b,.26,5.92,'recessed glass',5.32)
    for label,ai,bi in [('Guangdong return',2,3),('Beihai return',4,5)]:
        a,b=r[ai],r[bi];length=np.linalg.norm(b-a)
        for x in [-length*.25,length*.25]:
            face_probe(label+' projecting side balcony',a,b,x+.22,13.30,'carved pale stone',4.105)
    expect('clear crossing in front',[0,-3,3],[0,0,-1],None)
    expect('west attic stone above upper eaves',[.55,-5,31.40],[0,1,0],'carved pale stone',4.385)
    chars=scene.tri[scene.mi==scene.materials.index('letter bronze')]
    legend=chars[(chars[:,:,2].max(1)>8.05)&(chars[:,:,2].max(1)<8.70)]
    records.append({'label':'raised cultural palace inscription in bronze','triangles':len(legend),
                    'longitude_span_local_m':float(np.ptp(legend[:,:,0])),
                    'passed':bool(len(legend)>200 and 7.4<np.ptp(legend[:,:,0])<7.7)})
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
