"""Check the chamfered Shen Bao entrance, sign, railings, fluted pilasters, spandrel diamonds and roof."""
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
MODEL = 'huangpu-shen-bao-building'
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

    params=json.loads((PROJECT/'source/precise'/MODEL/'source/parameters.json').read_bytes())
    front=np.asarray(params['front_uv_m'])
    for face_index,(a,b,name) in enumerate(zip(front,front[1:],['Shandong Middle Road','Chamfer','Hankou Road'])):
        tangent=(b-a)/np.linalg.norm(b-a)
        normal=np.array([tangent[1],-tangent[0]])
        center=(a+b)/2
        def ray(label,u,z,material,d):
            pos=center+tangent*u+normal*2
            expect(name+' / '+label,[float(pos[0]),float(pos[1]),z],[-float(normal[0]),-float(normal[1]),0.],material,2-d)
        corner=face_index==1
        axes=[0.] if corner else [-5.10,-1.70,1.70,5.10]
        for k,x in enumerate(axes):
            ray('street opening '+str(k+1),x+.19,2.13,'entry glazing',-.447)
            for j,base in enumerate([5.08,8.95,12.51]):
                ray(f'office window in bay {k+1}, tier {j+1}',x+.17,base+1.25,'recessed glass',-.31)
                ray(f'metal grid in bay {k+1}, tier {j+1}',x,base+1.25,'bronze window frame',-.152)
            ray('attic louvre '+str(k+1),x+.17,16.44,'roof trim',-.145)
            if not corner:
                ray('diamond spandrel '+str(k+1),x+.352,12.143,'stone shade',.090)
                ray('diamond field '+str(k+1),x+.125,12.11,'warm stone',0.)
        if corner:
            ray('gold sign fascia field',1.12,3.94,'office granite',.177)
            ray('empty area above centre of chamfer between full balconies',.19,4.96,'warm stone',0.)
        else:
            for u in (-6.59,-3.4,0.,3.4,6.59):
                ray('pilaster central fillet '+str(u),u,13.56,'warm stone',.215)
                ray('recess at side of pilaster flute '+str(u),u+.035,13.56,'stone shade',.123)
            ray('projecting balcony coping',1.26,5.37,'office granite',.795)
        ray('deep roof ledge',.15,17.60,'stone shade',1.06)
    tri=scene.tri[scene.mi==scene.materials.index('aged bronze')]
    names=tri[:,:,0].mean(1)
    for low,hi,item in [(-.78,-.24,'申'),(-.22,.22,'報'),(.24,.78,'館')]:
        pick=tri[(names>low)&(names<hi)]
        records.append({'label':'raised entrance character '+item,'triangles':len(pick),'passed':bool(len(pick)>50 and pick[:,:,2].min()>3.72 and pick[:,:,2].max()<4.18)})
    expect('roof over retained study',[0,2,20],[0,0,-1],'roof skin',2.32)
    expect('street corner lane beyond the entrance',[0,-2,2],[0,0,-1],None)
    expect('unmodelled interior of the rear block',[0,22,2],[0,0,-1],None)
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
