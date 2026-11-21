from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-anting-villa-garden-arcade'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos, sin, pi
    samples = []
    def hit(label, x,y,z, direction, materials, distances):
        ray = scene.ray([x,y,z],list(direction),6)
        ok = ray is not None and ray['material'] in materials and distances[0] <= ray['distance_m'] <= distances[1]
        samples.append(dict(check=label, origin=[x,y,z], direction=list(direction), materials=materials, metres=list(distances), hit=ray, passed=bool(ok)))
    front=(0,1,0); down=(0,0,-1)
    for x in (-2.56,0,2.56):
        for height in (1.2,1.68,2.02):hit('stone post above terrace balustrade',x,-.48,height,front,['chalk stone'],(.428,.434))
        hit('advanced capital',x,-.51,2.408,front,['chalk stone'],(.373,.383))
        hit('square rail pier',x,-1.87,.49,front,['chalk stone'],(.182,.189))
    for cx in (-1.28,1.28):
        for degree in (16,32,49,66,83,100,117,134,151,165):
            t=degree*pi/180
            hit('raised limestone archivolt',cx+1.146*cos(t),-.39,2.36+1.146*sin(t),front,['chalk stone'],(.307,.322))
        for dx in (-.50,-.23,.23,.50):
            hit('arcade opening reaches recessed door glass',cx+dx,-.15,1.36,front,['door glass'],(1.77,1.80))
        for dx in (-.26,-.14,.18,.32):
            hit('arched fanlight behind the outer arch',cx+dx,.55,2.23,front,['door glass'],(1.10,1.12))
        hit('paired door leaves meet',cx,-.25,1.22,front,['dark walnut'],(1.847,1.869))
        hit('horizontal timber transom',cx,-.51,1.86,front,['dark walnut'],(2.08,2.14))
        for dx in (-1.02,1.02):
            hit('rear wall beside architrave',cx+dx,-.25,1.38,front,['warm reveal'],(1.80,1.82))
        for j in (0,1,3,4,6,7):
            x=cx+((j+.5)/8-.5)*(2.56-.17)
            hit('turned stone baluster',x,-1.8,.52,front,['chalk stone'],(.149,.175))
        for dx in (-.62,-.34,.34,.63):
            hit('stone coping',cx+dx,-1.55,1.25,down,['chalk stone'],(.29,.30))
        for dx in (-.60,-.30,.32,.62):
            hit('terrace behind low rail',cx+dx,-.60,.7,down,['terrace flags'],(.68,.70))
    for col in (1,4,7,9,12,15,19,22,25):
        x=-5.56/2+(col+.5)*5.56/28
        hit('rounded projecting red pan tiles',x,-.32,4.24,down,['russet tile','light fired tile'],(.25,.33))
    return dict(passed=all(s['passed'] for s in samples),samples=samples)


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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
