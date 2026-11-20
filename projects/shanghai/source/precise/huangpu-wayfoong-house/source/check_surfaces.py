"""Independently probe the street doors, window groups, cast-iron panels and light wells."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-wayfoong-house'
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
    for k in range(-2,3):
        x=k*5.91
        for dx in [-1.54,0,1.54]:
            for z in [8.48,12.50,16.52,20.54]:
                probe('narrow recessed casement',[x+dx+.14,-2,z+1.36],[0,1,0],'smoky window glass',2.42)
            for z in [26.36,29.42]:
                probe('upper attic casement',[x+dx+.14,-2,z],[0,1,0],'smoky window glass',2+.52+.345)
        probe('first-storey shop glazing',[x+.34,-2,1.68],[0,1,0],'smoky window glass',2.43)
        probe('upper pedestal glazing',[x+.34,-2,6.05],[0,1,0],'smoky window glass',2.43)
        probe('opaque decorated cast-iron panel',[x+1.40,-2,4.64],[0,1,0],'embossed cast iron',2-.136)
    for x in [-17.58,17.58]:
        probe('recessed residential doorway',[x+.36,-2,1.65],[0,1,0],'smoky window glass',2.87)
        for z in [8.48,12.50,16.52,20.54]:
            probe('rusticated wing window',[x+.27,-2,z+1.27],[0,1,0],'smoky window glass',2.42)
            probe('dark cast spandrel',[x+.92,-2,z+3.50],[0,1,0],'embossed cast iron',2-.136)
        probe('upper end pavilion',[x+.27,-2,33.04],[0,1,0],'smoky window glass',2+.52+.36)
        probe('independent pavilion roof',[x,4,39],[0,0,-1],'flat parapet roof',39-35.43)
    for x in [-8,5]:
        probe('open roof court lowered to second floor',[x,17,39],[0,0,-1],'flat parapet roof',39-8.03)
    for x in [-17,-1.2,16]:
        probe('raised roof return beside court',[x,17,39],[0,0,-1],'flat parapet roof',39-24.1)
    probe('rear service range',[0,26,39],[0,0,-1],'flat parapet roof',39-21.58)
    probe('upper street-wing roof',[3,6,39],[0,0,-1],'flat parapet roof',39-(31.84-.13))
    for x,y in [(0,-2),(22,6),(-22,6),(0,31)]:
        probe('outside the registered housing envelope',[x,y,39],[0,0,-1],None,None)
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
