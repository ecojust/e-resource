"""Sample the actual serialized riverfront façade; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-banque-de-lindochine'
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
    stone='Bund granite'
    trim='dressed pale granite'
    glass='green-grey glazing'
    for x in [-8.77,-4.56,4.56,8.77]:
        garden('four arched ground-floor glazed openings',x+.32,3.0,glass,7.402)
        garden('four crowned arch heads',x,6.72,trim,6.71)
    for x in [-8.77,-4.56,0,4.56,8.77]:
        garden('five windows behind balcony rails',x+.27,10.70,glass,7.402)
    for x in [-8.77,-5.20,-3.92,-1,0,1,3.92,5.20,8.77]:
        garden('nine top windows in five bays',x+.17,16.08,glass,7.402)
    for x in [-2.49,2.49]:
        garden('two giant smooth shafts',x,13.02,stone,6.15)
    for x in [-.55,.55]:
        garden('recessed door leaves',x,1.25,'portal oak',8.12)
    garden('stone portal lintel',0,4.86,trim,6.52)
    garden('paired broken pediment shoulder',1.67,5.46,trim,6.40)
    garden('portal central crest',0,5.88,trim,6.61)
    garden('top cornice lip',2.2,19.73,trim,6.38)
    for x in [-8.66,8.66]:
        garden('end parapet carved medallions',x,20.73,stone,6.72)
    for x in [-2.5,2.5]:
        garden('separate upper balustrade piers',x,20.40,stone,6.84)
    garden('open upper center between turned balusters',.64,20.26,None,None)
    for x,y in [(-13,0),(13,0),(0,3)]:
        check('no model in neighboring parcels or deep office block',[x,y,32],[0,0,-1],None)
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
