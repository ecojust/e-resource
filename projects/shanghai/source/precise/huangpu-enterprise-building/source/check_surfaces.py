"""Probe the actual office bays, current door, historic arched windows and stepped parapet."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-enterprise-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    import numpy as np
    rows=[]
    def probe(label,origin,direction,material,depth,tol=.043):
        hit=scene.ray(list(origin),list(direction),50)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<tol)
        rows.append(dict(label=label,origin=list(origin),direction=list(direction),reference_depth_m=depth,
                         expected_material=material,hit=hit,passed=ok))
    for k in range(-3,4):
        x=5.36*k
        for dx in [-1.22,0,1.22]:
            for level in range(6):
                z=8.42+3.58*level
                probe('brown-brick bay with recessed glazed casement',[x+dx+.11,-2,z+1.03],[0,1,0],'smoke green glass',2.395)
        if k:
            probe('high hall opening below springing',[x+.26,-2,6.16],[0,1,0],'smoke green glass',2.44)
            probe('arched upper centre',[x+.24,-2,7.21],[0,1,0],'smoke green glass',2.44)
            probe('filled arch shoulder',[x+1.59,-2,7.25],[0,1,0],'golden brown facing brick',2.0)
            probe('dark metal division at two-storey height',[x+.24,-2,3.51],[0,1,0],'dark patinated metal',2-.169)
        probe('projecting window stool',[x+.16,-2,8.42-.018],[0,1,0],'buff washed stone',2-.106)
    probe('recessed central street entrance',[.28,-2,1.64],[0,1,0],'smoke green glass',2.84)
    probe('stone entrance jamb',[1.70,-2,1.64],[0,1,0],'buff washed stone',2-(.098+.53/2))
    probe('dark nameboard below gold lettering',[1.90,-2,4.18],[0,1,0],'dark patinated metal',2-(.137+.22/2))
    for x,z in [(-3.12,32.95),(-2.52,33.64),(-1.73,34.23),(-.93,34.87),(0,35.28)]:
        probe('stepped crown coping',[x,.06,42],[0,0,-1],'buff washed stone',42-(z+.02))
    for x,y,height in [(5,5,30.40),(-21.6,16.5,30.40),(10,17,31.74),(0,24,30.40)]:
        probe('upper roof, jog or rear roof',[x,y,42],[0,0,-1],'flat roof membrane',42-height)
    for x,y in [(0,-2),(-21,3),(21,4),(3,28)]:
        probe('street or other property',[x,y,42],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
