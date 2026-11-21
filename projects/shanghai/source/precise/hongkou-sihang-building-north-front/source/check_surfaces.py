"""Check the northern end bay, independent hoods, curved balconies, fanlights and parapet."""
from argparse import ArgumentParser
import numpy as np
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-sihang-building-north-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,point,direction,length,wanted,lo=0,hi=20):
        hit=scene.ray(point,direction,length)
        ok=hit is None if wanted is None else bool(hit and hit['material']==wanted and lo<=hit['distance_m']<=hi)
        rows.append(dict(test=label,origin=list(map(float,point)),direction=list(map(float,direction)),length_m=length,expected_material=wanted,range_m=[lo,hi],hit=hit,passed=ok))
    centers=[-7.8,-3.97,-.14,3.69,7.52,11.35]
    for floor in range(6):
        z=5.0+floor*3
        for x in [-11.45,*centers]:
            if floor==0 and -8<x<.5:continue
            ray(f'window at {x} floor {floor+2}',[x+.14,-2,z+1.26],[0,1,0],4,'smoky blue window glazing',2.18,2.21)
        if floor<5:
            for x in centers:
                if floor==0 and -6.5<x<.5:continue
                ray(f'separate hood at {x} floor {floor+2}',[x,-.30,z+2.52],[0,0,-1],1,'blued grey canopy canvas',.54,.60)
    for x in centers:
        ray(f'open top balcony at {x}',[x+.18,-.29,20.90],[0,0,-1],1,'stone sill and canopy',.85,.89)
        ray(f'curved balcony railing of {x}',[x,-2,20.80],[0,1,0],3,'charcoal steel sash',1.35,1.46)
    for x in [-9.72,-5.885,-2.055,1.775,5.605,9.435]:
        ray(f'pale pier at {x}',[x,-2,15.30],[0,1,0],4,'weathered pale mineral render',1.79,1.84)
        ray(f'chevron pier crown at {x}',[x,-2,24.0],[0,1,0],4,'weathered pale mineral render',1.785,1.81)
        ray(f'sky above adjoining parapet near {x}',[x+.66,-2,23.9],[0,1,0],3,None)
    for x in [-6.69,-3.18,.33]:
        ray(f'fanlight round-top pane at {x}',[x+.075,-2,4.84],[0,1,0],3,'smoky blue window glazing',1.24,1.30)
        ray(f'fanlight center spoke at {x}',[x,-2,4.95],[0,1,0],3,'golden fanlight bars',1.19,1.25)
    ray('roof of street section',[2.4,1.2,26.7],[0,0,-1],6,'grey roof and study return',3.39,3.44)
    ray('open pavement in front of shop',[4.5,-.80,1.65],[0,0,-1],2,None)
    ray('at-grade shop glazing',[4.80,-1.1,1.4],[0,1,0],2,'smoky blue window glazing',1.26,1.33)
    return dict(passed=all(x['passed']for x in rows),samples=rows)


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
