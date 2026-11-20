"""Verify the north six-column window grid, triple fins, colored frieze, bronze panels and entrance steps."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-jialing-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def sample(label,origin,direction,material,position,tolerance=.040):
        hit=scene.ray(origin,direction,55)
        passed=hit is None if material is None else hit is not None and hit['material']==material and abs(hit['distance_m']-position)<tolerance
        rows.append(dict(label=label,origin=origin,direction=direction,expected_material=material,expected_distance=position,actual=hit,passed=passed))
    def front(label,x,z,material,y,tolerance=.040):
        sample(label,[x,-3,z],[0,1,0],material,3+y if y is not None else None,tolerance)
    columns=[-5.65,-2.28,-.83,.72,2.18,5.85]
    for i,x in enumerate(columns):
        for floor in [10.46,13.62,16.79,19.97,23.14,26.31]:
            z=floor+(.28 if i in [0,5]else 0)
            front('north elevation: six columns on six tiers',x+.23,z+.59,'blue-grey glazing',.40)
            front('upper transom of steel sash',x+.18,z+1.24,'painted steel frame',.345)
    for x in [-1.56,-.055,1.47]:
        front('continuous upper facade fin',x+.06,26.40,'grey-brown rendered masonry',-.19)
        front('fin extends above the wall coping',x,30.76,'grey-brown rendered masonry',-.19,.05)
    for x in [-5.79,6.0]:
        front('lower panel outer bronze rim',x+.605,2.41,'patinated bronze relief',.05)
        front('upper panel outer bronze rim',x+.615,7.18,'patinated bronze relief',.05)
        front('short fluting between bronze panels',x-.53,5.41,'patinated bronze relief',-.053)
    for x in [-7.4,6.85]:
        front('wing granite band',x,9.03,'dark polished granite',-.067)
        front('wing granite plinth',x,1.0,'dark polished granite',-.074)
    front('recessed entrance glazing',-.73,2.96,'blue-grey glazing',1.55)
    front('vertical recessed entrance frame',1.36,3.08,'painted steel frame',1.47)
    front('granite jamb alongside square portal',3.13,4.0,'pale grey granite',0)
    for i in range(4):
        sample('ascending granite stair tread',[.71,.29+i*.29,1.3],[0,0,-1],'dark polished granite',1.3-.135*(i+1))
    for x,z in [(-4.,29.81),(0,30.63),(4.,29.81)]:
        sample('two roof levels above the north elevation',[x,1.34,34],[0,0,-1],'plain section',34-z)
    for x in [-5.4,1.1,6.5]:
        roof=30.63 if abs(x)<2.75 else 29.81
        front('ochre frieze below projecting coping',x,roof-.21,'ochre parapet panels',.008)
    front('beyond eastern section',-8.95,7,None,None)
    front('beyond western section',8.55,7,None,None)
    sample('open beyond section depth',[0,2.21,32],[0,0,-1],None,None)
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
