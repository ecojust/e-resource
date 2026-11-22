from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-xiangde-66-no1-volute-portico'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import pi,cos,sin
    rows=[]
    def cast(feature,x,z,material,depth,tolerance=.012):
        hit=scene.ray([x,-.9,z],[0,1,0],1.50)
        if isinstance(material,str):material={material}
        rows.append(dict(feature=feature,x=x,z=z,materials=sorted(material),distance=depth,hit=hit,passed=hit is not None and hit['material'] in material and abs(hit['distance_m']-depth)<tolerance))
    for x in (-1.05,1.05):
        for z,radius in [(.04,.225),(.11,.221),(.324,.205),(.61,.204),(1.17,.202),(1.45,.2),(1.78,.195),(2.11,.19)]:
            cast('round shaft and stepped foot',x,z,{'washed aggregate','grey pebble','pale pebble'},.9-radius)
        for z,front in [(2.35,.246),(2.38,.256),(2.414,.253),(2.438,.273),(2.462,.283),(2.507,.290)]:
            for dx in (-.16,0,.16):cast('six distinct impost courses',x+dx,z,'moulded stone',.9-front)
        for sign in (-1,1):
            cx=x+sign*.142
            for dx,dz in [(.035,.019),(-.03,.018),(.02,-.036),(-.024,-.04)]:
                cast('circular rolled capital',cx+dx,2.254+dz,{'moulded stone','deep groove'},.666)
    for t in (.20,.40,.62,.85,1.08,2.04,2.29,2.51,2.73,2.95):
        for width,front,material in [(.023,-.236,'arch soffit'),(.059,-.246,'moulded stone'),(.095,-.208,'washed aggregate'),(.127,-.225,'moulded stone')]:
            cast('concentric projecting archivolt',( .737+width)*cos(t),2.52+(.555+width)*sin(t),material,.9+front)
        x=(.737-.065)*cos(t);z=2.52+(.555-.065)*sin(t)
        h=scene.ray([x,-.9,z],[0,1,0],1.5)
        rows.append(dict(feature='open beneath curved underside',x=x,z=z,hit=h,passed=h is None))
    for x in (-.066,-.033,0,.031,.072):
        for z in (3.09,3.16,3.239):cast('tapered projecting keystone',x,z,{'moulded stone','deep groove'},.630)
    for x in (-1.14,-.88,-.42,0,.44,1.11):
        cast('upper projecting stringcourse',x,3.41,'moulded stone',.633)
    return dict(samples=rows,passed=all(q['passed'] for q in rows))

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
