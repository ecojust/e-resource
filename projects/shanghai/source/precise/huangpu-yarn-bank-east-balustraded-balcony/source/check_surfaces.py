from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-yarn-bank-east-balustraded-balcony'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import pi,cos,sin,sqrt
    values=[]
    def shot(label,x,y,z,target,depth,tol=.025):
        r=scene.ray([x,y,z],[0,1,0],3.)
        values.append(dict(feature=label,origin=[x,y,z],observed=r,expected_depth=depth,passed=bool(r and r['material']in target and abs(r['distance_m']-depth)<tol)))
    for a in [-.77,-.57,-.41,-.23,0,.23,.41,.57,.77]:
        for z,edge,material in [(.63,.048,'warm grey limestone'),(.685,.075,'shadow fillet'),(.81,.018,'warm grey limestone'),(.874,.036,'sunlit rail moulding'),(1.41,.026,'shadow fillet'),(1.45,.055,'warm grey limestone'),(1.498,.071,'sunlit rail moulding')]:
            x=(1.64+edge)*sin(a);y=-.05-(.78+edge)*cos(a)
            shot('bowed course',x,-2,z,[material],2+y,.017)
    for j in range(11):
        a=((j+1)/12-.5)*pi;x=1.59*sin(a);y=-.05-.73*cos(a)
        shot('square individual foot',x,-2,.913,['light recessed course'],2+y-.07)
        shot('convex turned body',x,-2,1.090,['baluster body'],2+y-.079,.018)
        shot('narrow upper neck',x,-2,1.235,['baluster body'],2+y-.039,.014)
    for x in [-.59,.59]:
        shot('underside corbel',x,-2,.51,['cut stone return'],1.45)
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
