"""Sample the actual serialized tower and linking arcade; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-holy-trinity-bell-tower'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def check(label,origin,direction,material,distance=None):
        hit=scene.ray(origin,direction,65)
        ok=hit is None if material is None else (
            hit is not None and hit['material']==material and abs(hit['distance_m']-distance)<.04)
        rows.append(dict(label=label,origin=origin,direction=direction,expected=material,
                         expected_distance_m=distance,hit=hit,passed=ok))
    def garden(label,x,z,material,distance):
        check(label,[x,-7,z],[0,1,0],material,distance)
    for x in (-1.12,1.12):
        garden('two lower tower lights',x,1.95,'church glazing',4.115)
        garden('open paired bell lights between louvres',x,12.95,None,None)
        garden('angled louvres',x,12.66,'louvred shutter',4.202)
    garden('middle pointed light',.11,6.25,'church glazing',4.115)
    for x in (-1.65,-.825,0,.825,1.65):
        garden('blind arcade below belfry',x,10.42,'dark arch brick',4.02)
    for side in (-1,1):
        # A radial ray sees across the open stone parapet to the octagonal stage.
        check('open parapet above square belfry',[side*7,0,22.38],[-side,0,0],'terracotta spire',4.33)
        check('stone ring below slender spire',[side*7,0,30.5],[-side,0,0],'granite trim',5.056)
        check('raised dormers have deep pointed openings',[side*7,0,25.1],[-side,0,0],'dark arch brick',4.40)
        check('wall next to dormer opening',[side*7,.70,25.1],[-side,0,0],'terracotta spire',4.15)
        check('upper octagonal spire',[side*7,0,37],[-side,0,0],'terracotta spire',5.79)
    garden('metal staff and cross',0,47.62,'finial metal',6.961)
    for x in (-2.87,2.87):
        for y in (-2.87,2.87):
            check('four independent corner finials',[x,y,50],[0,0,-1],'finial metal',23.01)
    for x in (-10.47,-8.84,-6.78,-4.29):
        check('open through both sides of each arcade bay',[x,-7,1.60],[0,1,0],None)
    for x in (-11,-8,-5):
        check('unobstructed gallery path to the tower',[x,-1.22,1.60],[0,0,-1],'porch pavement',1.518)
    check('solid shaft between arch openings',[-7.50,-7,1.60],[0,1,0],'granite shaft',3.897)
    check('centerline reaches the actual tower door',[-12,-.95,1.70],[1,0,0],'oak door',9.23)
    check('shallow pitched gallery roof',[-8,-1.75,50],[0,0,-1],'slate roof',45.438)
    check('central gallery ridge',[-8.6,-.95,50],[0,0,-1],'slate roof',45.22)
    for xy in [(-15,5),(-5.2,1.51),(5,0),(1,-4)]:
        check('no geometry in neighboring nave, court or property',[*xy,50],[0,0,-1],None)
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
