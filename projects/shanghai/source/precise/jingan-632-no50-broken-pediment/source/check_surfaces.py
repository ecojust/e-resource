from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-632-no50-broken-pediment'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def shot(label,x,z,mat=None,distance=None):
        result=scene.ray([x,-.82,z],[0,1,0],1.30)
        ok=result is None if mat is None else (result is not None and result['material']==mat and abs(result['distance_m']-distance)<.013)
        rows.append(dict(feature=label,x=x,z=z,material=mat,expected_depth=distance,hit=result,passed=ok))
    for x in (-.29,-.17,0,.17,.29):
        for z in (.82,1.01,1.23,1.45,1.68,1.79):
            shot('open centre of broken pediment',x,z)
    for side in (-1,1):
        for t in (.044,.13,.22,.32,.40,.53,.62,.73,.81,.87):
            x=side*(.335+1.695*t)
            top=1.78-.45*t*t-.20*t
            shot('upper edge on the rising wing',x,top+.045,'weathered edge',.288)
            shot('projecting vertical fascia',x,top+.007,'light moulding',.309)
            if t==.87:
                shot('outer horizontal return precedes the raking fascia',x,top-.096,'light moulding',.288)
            else:
                shot('lower fascia beneath the upper lip',x,top-.096,'weathered edge',.375)
        for t in (.088,.245,.405,.562,.726):
            x=side*(.335+1.695*t);top=1.78-.45*t*t-.20*t
            if t==.726:
                shot('outer horizontal return meets the corbel',x,top-.249,'light moulding',.288)
            else:
                shot('nose of spaced corbel',x,top-.249,'pale stone',.344)
        for x in (.315,.57,.76,.92):
            shot('central stepped cornice',side*x,.641,'light moulding',.591)
            shot('flat middle bed',side*x,.607,'pale stone',.615)
        for x in (1.31,1.47,1.60):
            shot('stepped forward at either end',side*x,.641,'light moulding',.231)
            shot('side bed nearer the street',side*x,.607,'pale stone',.255)
    return dict(samples=rows,passed=all(q['passed']for q in rows))

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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
