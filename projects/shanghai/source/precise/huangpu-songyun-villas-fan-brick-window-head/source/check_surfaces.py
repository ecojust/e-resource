from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-songyun-villas-fan-brick-window-head'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    import runpy
    mod=runpy.run_path(str(SOURCE/'fan_brick_window.py'));point=mod['point_on_brick'];joints=mod['JOINTS'];results=[]
    def trace(label,x,z,depth,material):
        v=scene.ray([x,-.8,z],[0,1,0],1.10)
        results.append(dict(feature=label,x=x,z=z,expected_material=material,expected_distance_m=.8+depth,observed=v,passed=bool(v and v['material']==material and abs(v['distance_m']-(.8+depth))<.003)))
    for i,(a,b) in enumerate(zip(joints,joints[1:])):
        t=(a+b)/2
        for height in [.28,.72]:
            x,z=point(t,height);trace('radiating fired brick',x,z,-.034,mod['brick_name'](i))
        x,z=point(t,-.08);trace('projecting arched rim',x,z,-.071,'dark cap')
        x,z=point(t,-.17);trace('upper plaster spandrel',x,(z+2.25)*.5,.01,'render')
        if i in (1,4,6,8,10,13,16,18,20,23):
            x,z=point(t,.496);trace('split brick bed joint',x,z,-.017,'mortar')
    for x in [-.35,.31]:
        for z in [.48,.70,1.04,1.38]:trace('sash light',x,z,.149,'warm reflected glass' if x>0 and z>1 else 'blue reflected glass')
        trace('cross rail',x,.825,.086,'sash')
    for x in [-.60,0,.60]:
        for z in [.45,1.10,1.43]:trace('timber stile',x,z,.104,'sash')
    for i in range(11):trace('projecting eaves dentil',-.944+i*.187,2.31,-.076,'brown brick')
    return dict(samples=results,passed=all(s['passed'] for s in results))

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
