"""Sample the actual serialized street frontage; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-holy-trinity-cathedral'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def check(label,origin,direction,material,distance=None):
        hit=scene.ray(origin,direction,42)
        ok=hit is None if material is None else (
            hit is not None and hit['material']==material and abs(hit['distance_m']-distance)<.04)
        rows.append(dict(label=label,origin=origin,direction=direction,expected=material,
                         expected_distance_m=distance,hit=hit,passed=ok))
    def from_street(label,x,z,material,y):
        check(label,[x,-3,z],[0,1,0],material,3+y)
    # Travel through the real garden portico to the closed door of the nave.
    check('open round garden arch to oak doors',[.24,-7,2.10],[0,1,0],'oak door',7.55)
    check('solid corner of garden portico',[5.25,-7,1.35],[0,1,0],'red face brick',2.54)
    check('six-lobed rose glazing',[.08,-5,14.27],[0,1,0],'rose glazing',5.23)
    check('stone between lobes',[1.11,-5,14.25],[0,1,0],'granite trim',5.08)
    for index in range(-3,4):
        for z in [7.59,10.21]:
            check('two bands of seven recessed lancets',[1.34*index+.15,-3,z],[0,1,0],'church glazing',3.315)
    for sign in (-1,1):
        for bay in (1,2,4):
            y=(bay+.5)*29.78/6
            check('walk past outer arcade to enclosed aisle wall',[sign*14,y,.85],[-sign,0,0],
                  'red face brick',4.49)
        check('open paved aisle walk',[sign*10.78,12.03,2.8],[0,0,-1],'porch pavement',2.695)
        check('arcade roof surface',[sign*9.65,15.83,25],[0,0,-1],'slate roof',17.33)
        check('nave roof pitch',[sign*2.10,14,25],[0,0,-1],'slate roof',8.888)
        check('transept pitch',[sign*10,35.0,24],[0,0,-1],'slate roof',6.46)
    for x,y,z,expected in [
        (.11,41.0,26,13.85),(1.0,44.50,26,14.57),(-8,42.4,20,14.06),(8,42.4,20,14.06)]:
        check('barrel, round west end and its two low annex roofs',[x,y,z],[0,0,-1],'slate roof',expected)
    check('entrance pavement within porch',[.25,-2.80,2.0],[0,0,-1],'porch pavement',1.885)
    for label,o in [('garden beyond porch',[0,-6,25]),('school compound',[27,22,25]),('separate belfry',[22,-1.5,38])]:
        check(label,o,[0,0,-1],None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed'] for r in rows))


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
