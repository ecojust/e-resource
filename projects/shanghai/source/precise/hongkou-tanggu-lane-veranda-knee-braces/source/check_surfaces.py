from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-tanggu-lane-veranda-knee-braces'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    observations=[]
    def apply(label,x,z,materials,depth,tolerance=.008):
        hit=scene.ray([x,-.51,z],[0,1,0],1.48)
        accepted=(hit is None) if depth is None else bool(hit and hit['material'] in materials and abs(hit['distance_m']-depth)<tolerance)
        observations.append(dict(feature=label,x=x,z=z,expected_materials=materials,hit=hit,passed=accepted))
    for i in range(11):
        z=.19+i*.135
        apply('central load bearing post',.041,z,['oxblood paint','wood highlight'],.43)
    for s in (-1,1):
        for t in (.15,.22,.31,.40,.51,.61,.72,.80,.89):
            x=s*(.069+.648*t);z=1.184+.608*t
            apply('diagonal brace',x,z,['oxblood paint','dark metal'],.470,.018)
            apply('visible gap below brace',x,z-.166,[],None)
    for i in range(17):
        x=-1.46+i*.1825
        apply('structural plate below fascia',x,1.82,['dark red joinery'],.433)
        apply('weathered front fascia',x,1.928,['oxblood paint','wood highlight'],.423)
        apply('continuous projecting sill',x,1.998,['light paint'],.402)
    for u in range(14):
        x=.096+(1.475-.096)*u/14
        apply('vertical strip of panel',x+.011,2.353,['oxblood paint'],.470)
        apply('panel recess',x+.053,2.377,['dark red joinery'],.501)
        apply('alternating short horizontal strip',x+.041,2.182 if u%2 else 2.291,['oxblood paint'],.47)
    for i in range(10):
        apply('planks in plainer left bay',-1.45+.156*i,2.244,['aged board'],.493)
    return dict(samples=observations,passed=all(s['passed']for s in observations))

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
