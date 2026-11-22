from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-south-suzhou-warehouse-1929-tablet'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    hits=[]
    def ray(label,x,z,surface,mat,tol=.005):
        hit=scene.ray([x,-.5,z],[0,1,0],.88)
        hits.append(dict(feature=label,x=x,z=z,expected=mat,expected_distance=.5+surface,observed=hit,passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-(.5+surface))<tol)))
    for x in [-.88,-.80,-.52,-.2,0,.2,.52,.8,.88]:
        for z in [2.73,2.89,3.13]:ray('pale stone face',x,z,-.085,'pale date stone')
        ray('upper drip',x,3.244,-.099,'sill stone')
    for x in [-.54,.54]:ray('foot',x,2.113,-.085,'pale date stone')
    for x in [-1.2,-.72,-.24,.24,.72,1.2]:
        for z in [.53,.78,1.14,1.39]:ray('glazing behind bars',x,z,.177,'window glass')
        ray('middle frame',x,.935,.12,'plain iron')
    for x in [-1.444,-.48,.48,1.444]:
        for z in [.52,.77,1.11,1.37]:ray('main sash',x,z,.116,'plain iron')
    for x in [-.96,0,.96]:
        for z in [.53,1.37]:ray('thin glazing bar',x,z,.142,'plain iron')
    for x in [-1.2,-.7,0,.7,1.2]:
        ray('lintel',x,1.74,-.066,'lintel grey')
        ray('sill',x,.23,-.128,'sill stone')
    for x,z in [(-.538,2.44),(-.538,2.54),(-.19+.098,2.532),(-.19-.090,2.532),(-.19+.089,2.434),
                (.18+.098,2.550),(.18-.011,2.302),(.55+.098,2.532),(.55-.090,2.532),(.55+.089,2.434)]:
        ray('raised 1929 character',x,z,-.103,'date characters')
    for x in [-.19,.55]:ray('counter of the 9 remains open',x,2.532,-.085,'pale date stone')
    return dict(samples=hits,passed=all(d['passed']for d in hits))

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
