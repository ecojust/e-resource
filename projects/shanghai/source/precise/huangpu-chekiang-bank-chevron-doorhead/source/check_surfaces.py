from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-chekiang-bank-chevron-doorhead'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    hits=[]
    def ray(label,x,z,mat,front,tol=.012):
        r=scene.ray([x,-.5,z],[0,1,0],1.5)
        hits.append(dict(feature=label,origin=[x,-.5,z],expected_material=mat,expected_depth=front,observed=r,passed=bool(r and r['material']==mat and abs(r['distance_m']-.5-front)<tol)))
    for j,(extent,drop,tip)in enumerate([(.535,.548,.152),(.457,.456,.251),(.371,.364,.356)]):
        for sign in [-1,1]:
            for t in [.12,.26,.40,.56,.70,.86]:
                a=extent*t;z=tip+(drop/extent)*a+.023
                ray('folded V rib',sign*a,z,'chevron face',-.038-.009*j)
    for sign in (-1,1):
        for distance in [.12,.18,.24,.30,.34]:
            for extent,drop,tip in [(.535,.548,.152),(.457,.456,.251)]:
                ray('exposed dark channel between two ribs',sign*distance,tip+drop*distance/extent+.074,'black recess',.031)
    for x in [-.64,.64]:
        for i,(z,depth)in enumerate([(.680,.029),(.566,.029),(.472,.014),(.405,.014),(.351,.014),(.305,.014),(.264,.014)]):
            ray('rounded side pendant',x,z,'beaded pendant',-.078-depth)
        for z in [.16,.29,.33,.44,.60]:
            ray('recessed apron between beads',x+.055,z,'finial apron',-.068)
    for x in [-1.04,1.07]:
        for z in [.08,.25,.34,.55,.78]:ray('stone jamb return',x,z,'brown dressed stone',-.002)
    for x in [-.84,-.76,-.35,.17,.61,.81]:ray('outer head rail',x,.803,'bronze border',-.015)
    return dict(passed=all(v['passed']for v in hits),samples=hits)

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
