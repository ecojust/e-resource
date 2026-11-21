"""Check Sichuan Street transoms, giant-order columns, arcades, consoles and the retained north base."""
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
ID='huangpu-asia-realty-sichuan-front'
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
    glass='smoky blue glass'
    trim='carved pale stone'
    for x in [-11.34,-5.67,0,5.67,11.34]:
        for level in [8.75,12.02,15.29,18.56]:
            for dx in [-1.18,0,1.18]:
                ray(f'triple window {x}/{dx} at {level}',[x+dx+.12,-2,level+.87],[0,1,0],3,glass,2.38,2.45)
        for dx in [-.88,.88]:
            ray(f'paired attic lights {x}/{dx}',[x+dx+.16,-2,22.16],[0,1,0],3,glass,2.38,2.45)
    for x in [-17.31,17.31]:
        for level in [8.75,12.02,15.29,18.56]:
            for dx in [-.60,.60]:
                ray(f'paired end windows {x}/{dx} at {level}',[x+dx+.18,-2,level+.93],[0,1,0],3,glass,2.05,2.15)
        ray(f'pillar rustication {x}',[x+2.29,-2,14.20],[0,1,0],3,'warm grey ashlar',1.60,1.75)
    for x in [-14.04,-8.96,-8.02,-2.94,2.94,8.02,8.96,14.04]:
        ray(f'giant shaft {x}',[x,-2,4.1],[0,1,0],3,trim,1.50,1.62)
    for x in [-11.18,-5.80,5.80,11.18]:
        ray(f'tall bank glass {x}',[x+.17,-2,6.15],[0,1,0],4,glass,2.81,2.92)
        ray(f'window balustrade {x}',[x+.12,-2,.87],[0,1,0],3,trim,1.75,1.88)
    for x,h,w in [(0,2.86,2.13),(17.31,3.46,3.49)]:
        ray(f'recessed gate double leaves {x}',[x+w*.245,-2,1.33],[0,1,0],4,'deep green door panels',2.25,2.37)
        if x==0:ray('central door border at leaf edge',[.21,-2,1.33],[0,1,0],4,'aged door metal',2.25,2.30)
        ray(f'fanlight at portal {x}',[x+.21,-2,h+1.10],[0,1,0],4,glass,2.35,2.41)
        ray(f'step below gate {x}',[x,-.31,1],[0,0,-1],2,'grey granite plinth',.885,.905)
    for x in [-8.50,-2.835,2.835,8.50]:
        ray(f'curved cornice console {x}',[x-.23,-2,24.20],[0,1,0],3,trim,1.25,1.85)
    for x in [-17.31,0,17.31]:
        roof=25.71 if x else 25.15
        ray(f'roof flashing {x}',[x,2.3,27],[0,0,-1],4,'grey roof flashing',27-roof-.05,27-roof+.05)
    ray('street outside ledge',[7,-1.5,1],[0,0,-1],2,None)
    ray('uncaptured north entrance retained from original source',[-17.31,-2,2],[0,1,0],2.8,None)
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
