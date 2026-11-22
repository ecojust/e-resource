from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='pudong-xie-shops-hongxi-lane-three-transom'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    slats=['aged timber','weathered timber','pale timber edge']
    def shoot(u,v,wood,label):
        o=[(u-126)*.004,-.30,(90-v)*.004];hit=scene.ray(o,[0,1,0],.6)
        passed=bool(hit and hit['material'] in slats and .300<=hit['distance_m']<=.305) if wood else hit is None
        samples.append(dict(feature=label,rectified_xy=[u,v],origin=o,direction=[0,1,0],hit=hit,passed=passed))
    # Positions measured along the contrast of the pictured wooden members,
    # including straight-through rays at bright control openings and shadowed voids.
    for v,present,absent in [(24,[16,32,84,100,168,204,220],[66,152,186,238]),
                              (40,[16,50,66,84,118,135,152,186,204],[32,100,168,220]),
                              (56,[16,50,66,84,118,135,152,168,186,221],[33,100,204]),
                              (71,[32,50,84,100,118,152,186,204,220,238],[66,134,168])]:
        for u in present:shoot(u,v,True,'continuous horizontal member')
        for u in absent:shoot(u,v,False,'open end of stepped return')
    for v,present,absent in [(32,[24,41,75,92,126,143,160,177,194,229],[212]),
                              (48,[24,41,92,109,143,160,194,212,229],[58,75,126,177]),
                              (63,[41,58,75,92,109,126,143,160,177,212],[194,229]),
                              (79,[41,58,75,126,143,160,177,194,229],[92,109,212])]:
        for u in present:shoot(u,v,True,'vertical timber face')
        for u in absent:shoot(u,v,False,'open side of staggered rectangle')
    for u in (33,68,118,151,202,238):
        for v in (33,47,63,79):shoot(u,v,False,'clear interior of lattice opening')
    return dict(samples=samples,passed=all(x['passed']for x in samples))

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
