"""Probe the National YWCA street sashes, recessed portal, sign, tiled eave and two upper setbacks."""
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
MODEL = 'huangpu-national-ywca'
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

    doc=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    plan=np.array(doc['study_uv_m'])
    cx=(plan[0,0]+plan[1,0])/2
    front_y=(plan[0,1]+plan[1,1])/2
    def east(label,x,z,mat,y):
        expect(label,[x,-3,z],[0,1,0],mat,None if y is None else y+3)
    for i,x in enumerate([-12.07,-7.00,-3.50,0,3.50,7.00,12.07]):
        for j,z in enumerate([6.02,10.26,13.96,17.70,21.56]):
            east(f'window strip {i+1}, upper row {j+1}',cx+x+.27,z,'recessed glass',front_y+.32)
    east('near doorway timber backing rather than a facade plane',cx+.32,2.06,'portal timber',front_y+.865)
    for sg in [-1,1]:
        east('blue jamb lamp '+str(sg),cx+sg*1.30,2.98,'blue lamp glass',front_y-.542)
    east('entrance threshold clear above the step',cx+.25,.48,'portal timber',front_y+.865)
    east('seventh floor genuinely set back',1.97,25.55,'recessed glass',2.99)
    east('eighth floor central bay set back again',.25,28.62,'recessed glass',4.75)
    east('clear roof outside the central tower',10.75,28.58,None,None)
    expect('Yuanmingyuan Road sidewalk clear',[0,-2.30,3],[0,0,-1],None)
    for mat,label,interval in [('glazed tile','small tile cylinders at the portal eaves',(5.00,5.42)),('portal timber','physical right-to-left lintel inscription',(4.52,4.73))]:
        tris=scene.tri[scene.mi==scene.materials.index(mat)]
        select=tris[(tris[:,:,2].min(1)>=interval[0])&(tris[:,:,2].max(1)<=interval[1])]
        width=float(np.ptp(select[:,:,0])) if len(select) else 0
        records.append({'label':label,'triangles':len(select),'width_m':width,'passed':bool(len(select)>90 and 1.8<width<2.4)})
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
