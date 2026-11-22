from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-shanyin-274-paired-brick-arches'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import pi,sin,cos
    rows=[]
    def depth(name,x,z,mat,dist,tol=.008):
        h=scene.ray([x,-.5,z],[0,1,0],.96)
        rows.append(dict(feature=name,x=x,z=z,expected=sorted(mat),depth_m=dist,hit=h,
                         passed=bool(h and h['material'] in mat and abs(h['distance_m']-dist)<tol)))
    for cx in (-.698,.698):
        for j in range(23):
            a=pi*(j+.5)/23
            depth('individual arched facing brick',cx+.575*cos(a),1.507+.575*sin(a),
                  {'red brick','light facing brick','dark facing brick'},.468)
        for sign in (-1,1):
            for j in (1,4,7,10,13,15):
                z=.108+(j+.5)*.0739
                depth('red jamb course',cx+sign*.586,z,{'red brick','light facing brick','dark facing brick'},.466)
        for dz in (.401,.715,1.215):
            for u in (-.36,-.125,.119,.348):depth('glass behind timber',cx+u,dz,{'glass'},.62)
            for u in (-.248,0,.248):depth('upright timber bar',cx+u,dz,{'red timber'},.568)
        for u in (-.374,-.104,.101,.358):depth('upper fan glass',cx+u,1.712,{'glass'},.62)
        for u in (-.39,-.16,.19,.39):
            depth('exposed grey brick course above the arch',cx+u,2.21,{'old grey brick','brick shade'},.505)
            depth('solid red panel between bottom rails',cx+u,.232,{'red timber'},.580)
        for u in (-.27,.043,.34):
            depth('transom rail',cx+u,1.511,{'red timber'},.565)
            depth('outer sill',cx+u,.097,{'pale stone sill'},.418)
    return dict(samples=rows,passed=all(r['passed']for r in rows))

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
