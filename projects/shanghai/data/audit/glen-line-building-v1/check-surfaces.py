"""Probe the Glen Line front, canted oriel, corner, crown, cornice and both inscriptions."""
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
MODEL = 'huangpu-glen-line-building'
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
                        'material':material,'expected_distance_m':depth,'first_hit':hit,'passed':bool(passed)})

    def east(label,x,z,y,mat='recessed glass'):
        expect(label,[x,-3,z],[0,1,0],mat,None if y is None else y+3)

    axes=[-4.48,-.68,1.46,3.60,7.48]
    for i,x in enumerate(axes):
        east(f'ground entrance or arched opening {i+1}',x+.16,1.24,.32)
        for j,z in enumerate([5.65,10.44,14.27,18.18,23.03]):
            y=-.11 if i==2 and j in (2,3) else .32
            east(f'river-facing axis {i+1}, window tier {j+1}',x+.13,z,y)
    for i,x in enumerate([-.68+1.07,1.46+1.07]):
        east(f'entrance stone support {i+1}',x,1.9,-.366,'carved pale stone')
    for i,x in enumerate([(-4.48-.68)/2-.07,(3.60+7.48)/2+.07]):
        east(f'pilaster shaft relief {i+1}',x,15.1,-.325,'upper stone')
    for x in [-5.03,6.65]:
        east('upper setback wing sash '+str(x),x+.13,27.28,2.68)
        expect('upper wing terrace slab '+str(x),[x,5.04,32],[0,0,-1],'roof',2.60)
    east('central tower arched window',1.61,27.11,1.60)
    east('stepped tower, lower stage',1.61,30.1,1.44,'upper stone')
    east('stepped tower, upper stage',1.61,34.35,2.17,'upper stone')
    east('outside tower above the outer eave',7.6,31.0,None,None)
    expect('clear east pavement ground',[3,-2.2,1.9],[0,0,-1],None)
    expect('clear Beijing East Road',[-15,11,1.9],[0,0,-1],None)
    expect('west cut flat roof',[-2,12,30],[0,0,-1],'roof',3.60)
    # Ray aligned with the central rounded southeast bay. The effective curved
    # sash depth varies with the faceted tangent, so query a material interval.
    for z in [1.24,5.65,10.44,14.27,18.18,23.03]:
        a=.748
        n=np.array([-3.83*math.cos(a),-3.19*math.sin(a),0]);n/=np.linalg.norm(n)
        surface=np.array([-5.61-3.19*math.cos(a),3.83-3.83*math.sin(a),z])
        o=surface+2*n
        hit=scene.ray(o,-n,4)
        records.append({'label':f'curved southeast sash at {z:.2f}m','origin_m':o.tolist(),'direction':(-n).tolist(),'first_hit':hit,
                        'passed':bool(hit and hit['material']=='recessed glass' and 2.28<hit['distance_m']<2.38)})
    letters=scene.tri[scene.mi==scene.materials.index('letter brass')]
    for name,low,high,min_width in [('English clearing-house frieze',8.85,9.34,8.0),('five Chinese crown characters',30.05,30.78,3.8)]:
        selection=letters[(letters[:,:,2].min(1)>=low)&(letters[:,:,2].max(1)<=high)]
        width=float(np.ptp(selection[:,:,0])) if len(selection) else 0
        records.append({'label':name,'material':'letter brass','triangles':len(selection),'width_m':width,'passed':bool(len(selection)>200 and width>min_width)})
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
