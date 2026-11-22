from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-wuyi-234-four-flue-chimney'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import cos,sin,pi
    rows=[]
    def hit(origin,direction,mat,dist,label):
        v=scene.ray(origin,direction,4);ok=bool(v and v['material'] in mat and abs(v['distance_m']-dist)<.006)
        rows.append(dict(feature=label,origin=origin,direction=direction,expected_material=mat,expected_distance=dist,hit=v,passed=ok))
    for cx in [-.61875,-.20625,.20625,.61875]:
        for x,y in [(0,0),(.06,0),(-.06,0),(0,.06),(0,-.06)]:hit([cx+x,y,3],[0,0,-1],['flue shadow'],.655,'five rays descend into each of the four open pipes')
        for angle in range(0,360,45):
            x=cx+.126*cos(pi*angle/180);y=.126*sin(pi*angle/180)
            hit([x,y,3],[0,0,-1],['sooty clay lip'],.307,'circle of surviving rim')
        for x,y in [(.17,.19),(-.17,.04),(.05,-.20)]:hit([cx+x,y,3],[0,0,-1],['sill mortar'],.42,'flat brick bedding between pipe and crown edge')
    for x in [-.69,-.49,-.18,.04,.18,.38,.66]:
        for z,dist in [(1.308,.697),(1.664,.704),(1.735,.681),(1.809,.658),(1.876,.632)]:
            hit([x,-1,z],[0,1,0],['corbel edge'],dist,'five projecting longitudinal bands')
    for x in [-.269,.275]:
        for z in [.32,.77,1.15,1.48,1.88,2.06,2.30]:
            hit([x,-1,z],[0,1,0],['mortar'],.741,'rebated vertical line on the long side')
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
