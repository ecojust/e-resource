from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-husi-warehouse-ribbed-iron-plates'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def ray(label,x,z,mat,dist):
        result=scene.ray([x,-.46,z],[0,1,0],2.)
        ok=bool(result and result['material']==mat and abs(result['distance_m']-dist)<.011)
        rows.append(dict(label=label,x=x,z=z,expected_material=mat,expected_distance_m=dist,observed=result,passed=ok))
    for x in [-.75,-.60,-.47,-.31,.32,.46,.60,.75]:
        for label,z,mat,dist in [('lower sill',.387,'umber brick',.419),('brick step 1',.444,'dark red brick',.431),('brick step 2',.483,'umber brick',.405),('brick step 3',.535,'dark red brick',.388),('brick step 4',.58,'umber brick',.368),('fascia below grey cap',.63,'umber brick',.316),('upper fascia',.694,'umber brick',.320),('wide cap',.734,'weathered cap',.284)]:
            ray(label,x,z,mat,dist)
    for x in [-.125,.125]:
        for dx,dz in [(-.065,-.034),(.066,-.036),(-.059,.036),(.062,.036),(.034,.082),(-.033,.082),(.042,-.088),(-.040,-.088)]:
            ray('flat pocket between raised ribs',x+dx,.528+dz,'iron casting',.424)
        for dx,dz in [(0,0),(-.012,0),(.012,0),(0,.012),(0,-.012)]:
            ray('raised central bolt head',x+dx,.528+dz,'iron pin',.367)
        for dx,dz in [(-.116,-.122),(.113,-.119),(.114,0),(.108,.119),(-.107,.12),(-.113,.005)]:
            ray('raised radial iron rib',x+.004+dx*.58,.528+dz*.58,'iron ridge',.391)
    return dict(passed=all(x['passed'] for x in rows),samples=rows)

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
