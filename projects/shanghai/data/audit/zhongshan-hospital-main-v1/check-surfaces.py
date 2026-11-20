"""Probe the photographed main elevation, five dormers, wing joins, ridge and terraces."""
import argparse
import math
import numpy as np
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[2]
MODEL = 'xuhui-zhongshan-hospital-main-building'
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

    for side,name in [(1,'north'),(-1,'south')]:
        direction=[0,-side,0]
        for floor in range(4):
            for u in [-12.78,8.52]:
                expect(f'{name} ward {floor+1} glazed bay {u}',[u+.28,side*11,3.87*floor+1.35],direction,'dark blue grey glazing',2.57)
        expect(name+' red brick pier',[3.195,side*11,5.88],direction,'weathered red brick',2.198)
        expect(name+' upper colonnade',[-25.85,side*11,18.1],direction,'light cast stone',2.465)
        expect(name+' projecting stone rail',[1.12,side*11,16.68],direction,'pale horizontal band',1.98)
    expect('north central bronze doors',[.54,11,1.10],[0,-1,0],'dark bronze door',2.57)
    expect('stone canopy from above',[1.45,9.65,5.03],[0,0,-1],'pale horizontal band',1.28)
    for i,(u,w) in enumerate([(-15.6,2.22),(-8,2.24),(0,4.63),(8,2.24),(15.6,2.22)]):
        level=20.3+4.85*(1-7.57/9.92)**1.43+.41
        expect(f'dormer {i+1} glazing',[u+.24,-9.9,level],[0,1,0],'dark blue grey glazing',2.65)
    for x in (-20.,.3,20.):
        expect('continuous yellow main ridge '+str(x),[x,0,30],[0,0,-1],'amber glazed crests',4.475)
    expect('free space beyond south eaves',[0,-12,26],[0,0,-1],None)
    expect('free space beyond north eaves',[0,12,26],[0,0,-1],None)
    for s in [-1,1]:expect('matching east-west ground wing joins',[s*27.6,0,17.5],[0,0,-1],'terrace paving',2.04)
    def exterior(label,origin,direction,material,depth,distance_tolerance=.04,filtered=False):
        wanted=(lambda name:name==material) if filtered else None
        hit=scene.ray(origin,direction,30,material_filter=wanted)
        facing=None
        if hit:
            a,b,c=scene.tri[hit['triangle_index']]
            normal=np.cross(b-a,c-a)
            facing=float(np.dot(normal,direction)/np.linalg.norm(normal))
        passed=bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<distance_tolerance and facing<-.05)
        records.append({'label':label,'origin_m':origin,'direction':direction,'material':material,
                        'expected_distance_m':depth,'actual_normal_dot_ray':facing,'first_hit':hit,'passed':passed})
    for side in [-1,1]:
        exterior('upper gable from its exterior',[side*30,1.11,23.3],[-side,0,0],'red gable and dormers',5.85)
        exterior('yellow end hip from above',[side*26.0,.64,29.0],[0,0,-1],'warm glazed yellow tile',7.32,.32,True)
        exterior('timber soffit under projecting eaves',[10.4,side*9.79,18],[0,0,1],'brown rafter tails',2.22,.12)
    for u,w in [(-15.6,2.22),(-8.0,2.24),(0.0,4.63),(8.0,2.24),(15.6,2.22)]:
        for side in [-1,1]:
            exterior('outward face of dormer cheek',[u+side*(w/2+1.2),-6.60,21.82],[-side,0,0],'red gable and dormers',1.20)
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
