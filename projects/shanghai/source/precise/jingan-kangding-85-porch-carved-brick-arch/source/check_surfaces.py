from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-kangding-85-porch-carved-brick-arch'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']






def test(scene, role):
    source=runpy.run_path(str(SOURCE/'porch_arch.py'))
    n=36 if role=='lod' else 60
    rows=[]
    def cast(name,x,y,z,material):
        hit=scene.ray([x,-.81,z],[0,1,0],1.45)
        ok=hit is not None and hit['material']==material and abs(hit['distance_m']-(y+.81))<.018
        rows.append(dict(feature=name,target=[x,y,z],expected=material,hit=hit,passed=ok))
    for i in range(3,n-3):
        t=(i+.5)/n
        x,y,z=source['course'](t,.244,-.011)
        # At the ends, the projecting capital cap lies in front of the arch face.
        if 1.12 < z < 1.18 and abs(abs(x)-2.21) < .79:
            cast('springing behind projecting abacus',x,-.15,z,'weathered terracotta')
        else:
            cast('radial intrados brick',x,y,z,source['BRICK'][(i*7+1)%len(source['BRICK'])])

        x,y,z=source['course']((i+.74)/n,.872,-.009)
        cast('outer brick course',x,y,z,source['BRICK'][(i*7+3)%len(source['BRICK'])])
    for j in range(1,10):
        x=(j-5)*.19
        hit=scene.ray([x,-.81,.38],[0,1,0],1.4)
        rows.append(dict(feature='clear opening',x=x,z=.38,hit=hit,passed=hit is None))
    for c in [-2.21,2.21]:
        for i in range(5):
            cast('capital abacus',c+(i-2)*.21,-.15,1.15,'weathered terracotta')
    return dict(samples=rows,passed=all(r['passed'] for r in rows))
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
