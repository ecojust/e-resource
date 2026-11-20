"""Sample the actual serialized first Morris Residence; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-ruijin-guesthouse-01'
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
    glass='residence glazing'
    brick='garden brick'
    for x in [-14.71,-8.86,-6.87,5.04,6.90,8.76,10.62,12.48]:
        for z in [1.87,5.72]:
            garden('stone end, paired east and five west garden windows',x+.17,z,glass,7.427)
    for x in [-3.58,-.25,2.66]:
        garden('entrance upper windows',x+.15,6.02,glass,7.747)
    garden('unfenestrated east brick wall',-12.45,3.05,brick,7.05)
    for x in [-2.10,-1.58,1.37,1.89]:
        garden('four front Tuscan shafts',x,2.14,'grey dressed stone',2.14)
    garden('open colonnade reaches the doors',.24,1.17,'entrance oak',8.342)
    garden('open ground beneath balcony',-.69,1.86,glass,8.304)
    garden('balcony frieze',0,4.28,'darkened stone',1.96)
    for x,z in [(-12.9,5.4),(-7.8,5.4),(11.55,6.02)]:
        garden('historic red masonry between windows',x,z,brick,7.05)
    for x,y,top in [(-13.82,2.46,12.92),(-2.01,6.82,12.00),(4.98,7.71,12.15),(11.52,3.47,12.92)]:
        check('four raised chimney caps',[x+.20,y,25],[0,0,-1],'chimney shadow',25-top-.0605)
    check('floor remains open to courtyard entrance',[0,-2.64,2.02],[0,0,-1],'garden threshold',1.87)
    check('unsupported interior treated as enclosed',[-2.55,17.22,2],[0,0,-1],'darkened stone',1.91)
    for x,y in [(0,-8.1),(22,1.7),(-23,12),(0,25)]:
        check('no model in adjacent gardens or neighboring villas',[x,y,27],[0,0,-1],None)
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
