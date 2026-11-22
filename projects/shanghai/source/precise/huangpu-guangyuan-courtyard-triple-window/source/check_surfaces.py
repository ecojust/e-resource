from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-guangyuan-courtyard-triple-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos,sin,pi
    values=[]
    def shot(name,x,z,mats,expected):
        r=scene.ray([x,-.5,z],[0,1,0],1.2)
        values.append(dict(feature=name,origin=[x,-.5,z],materials=mats,expected_depth=expected,observed=r,passed=bool(r and r['material']in mats and abs(r['distance_m']-.5-expected)<.013)))
    for i,d in enumerate(['warm glass','shaded glazing','glass in shade']):
        x=-.8+(i+.50)*1.6/3
        for z in [1.02,1.21,1.45,1.66,1.92]:shot('three vertical glazed lights',x,z,[d],.132)
    for x in [-.8+1.6/3,-.8+3.2/3]:
        for z in [1.01,1.2,1.41,1.64,1.88,2.00]:shot('timber mullion',x,z,['weathered wooden stiles'],.014)
    for x in [-.69,-.4,-.204,.206,.403,.692]:
        shot('projecting sill return',x,.846,['lit stone fillet'],-.096)
        shot('upper apron band',x,.776,['stone fascia'],-.061)
        shot('recessed apron',x,.652,['buff render return'],-.043)
    for i in range(24):
        a=(i+.5)*2*pi/24;shot('shallow oval cartouche rim',.145*.885*cos(a),.648+.074*.885*sin(a),['raised oval rim'],-.064)
    for x in [-.06,0,.06]:shot('plain oval centre',x,.648,['oval recess'],-.057)
    for z in [1.01,1.23,1.46,1.66,1.88,2.02]:
        for x in [-1.01,1.01]:shot('coursed window sides',x,z,['sand render'],-.02)
    return dict(passed=all(v['passed']for v in values),samples=values)

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
