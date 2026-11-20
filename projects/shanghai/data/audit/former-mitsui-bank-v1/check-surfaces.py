"""Check all flanking and central windows, six faceted columns, the 50 Jiujiang Road doors, ironwork and bank sign."""
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
MODEL = 'huangpu-former-mitsui-bank'
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

    def street(label,x,z,y,material):
        expect(label,[x,-2,z],[0,1,0],material,None if y is None else y+2)

    for k,x in enumerate([-8.79,-7.05,-1.72,0.,1.72,7.05,8.79]):
        for j,z in enumerate([9.48,12.74,16.,19.26]):
            street(f'upper bay {k+1}, tier {j+1}, recessed glass',x+.18,z+.65,2.89,'glass')
            street(f'upper bay {k+1}, tier {j+1}, sash transom',x+.17,z+1.06,2.7275,'sash')
    for i,x in enumerate([-10.08,-5.27,-3.62,3.62,5.27,10.08]):
        street(f'cut-corner shaft {i+1}',x+.18,14.0,.59,'granite ashlar')
        street(f'three lines on shaft {i+1}',x+.34,14.0,.5835,'stone joint')
        street(f'cap {i+1}, angular boss',x,22.30,.417,'granite ashlar')
        street(f'cap {i+1}, projecting rebate',x+.025,22.18,.390,'recessed stone')
    for x in [-1.,1.]:
        for z in [1.14,2.66,4.12]:
            street(f'octagonal bronze moulding, leaf {x}, height {z}',x+.61,z,.805,'raised bronze')
        street(f'central convex boss of leaf {x}',x+.08,2.66,.79,'bronze iron')
        street(f'leaf {x}, perimeter beads',x+.85,.39,.80,'raised bronze')
    for x in [-8.20,8.20]:
        step=(6.88-.35)/4
        for k in range(4):
            z=.79+.18+step*(k+.5)
            street(f'circle of iron on flank {x}, cell {k+1}',x+(2.54-.36)*.7*.31,z,.728,'bronze iron')
            street(f'decorative grille octagon on flank {x}, cell {k+1}',x+(2.54-.36)*.7/2-.025,z,.716,'raised bronze')
        street(f'grille side rod {x}',x+(2.54/2-.23),4.50,.716,'bronze iron')
    for x in [-5.,5.]:
        street(f'inset framed stone field {x}',x+1.265,4.,.403,'recessed stone')
    for number,z,x in [(1,23.06,-11.48),(7,23.06,0.),(13,23.06,11.48)]:
        street(f'under-cornice bracket {number}',x+.06,z,.075,'recessed stone')
    for name,material,zlo,zhi,minimum in [
        ('cast street number 50','raised bronze',5.24,5.54,80),
        ('modern six Chinese characters','sign letters',8.61,9.17,350),
        ('modern English sign inscription','sign letters',8.25,8.55,700),
        ('construction-bank blue logo','blue enamel',8.05,9.25,16)]:
        ts=scene.tri[scene.mi==scene.materials.index(material)]
        ts=ts[(ts[:,:,2].min(1)>zlo)&(ts[:,:,2].max(1)<zhi)]
        if 'number' in name:ts=ts[(ts[:,:,0].min(1)>-.30)&(ts[:,:,0].max(1)<.30)]
        records.append({'label':name,'triangles':len(ts),'passed':bool(len(ts)>=minimum)})
    expect('front sectional roof',[1.,3.,30.],[0,0,-1],'roof coping',5.87)
    expect('free pavement in front of colonnade',[0.,-1.1,2.],[0,0,-1],None)
    expect('old building north of new section',[0.,6.,4.],[0,0,-1],None)
    expect('retained frontage past east stop',[13.5,2.,2.],[0,0,-1],None)
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
