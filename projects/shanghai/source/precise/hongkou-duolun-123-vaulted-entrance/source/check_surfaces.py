from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-duolun-123-vaulted-entrance'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import pi,sin,cos
    rows=[]
    def check(name,origin,vector,limit,materials,expected=None,tol=.018):
        hit=scene.ray(origin,vector,limit)
        if materials is None:
            ok=hit is None
        else:
            ok=bool(hit and hit['material'] in materials and
                    (expected is None or abs(hit['distance_m']-expected)<=tol))
        rows.append(dict(feature=name,origin=origin,vector=vector,max_distance_m=limit,
                         allowed_materials=sorted(materials) if materials else [],expected_depth_m=expected,hit=hit,passed=ok))
    for frac in (.065,.125,.19,.27,.36,.455,.515,.61,.70,.79,.875,.935):
        a=pi*frac
        for r,front,mat in [(.945,-.817,'worn stone edge'),(.969,-.842,'pale dressed stone'),
                            (1.019,-.825,'pale dressed stone'),(1.071,-.842,'worn stone edge'),
                            (1.094,-.852,'pale dressed stone')]:
            check('five front curved stone mouldings',[r*cos(a),-1.34,2.51+(r-.179)*sin(a)],[0,1,0],.70,{mat},1.34+front)
    for x in (-1.06,1.06):
        for z in (.041,.202,.445,.77,1.12,1.57,2.05,2.31):
            mat='plinth stone' if z<.5 else 'pale dressed stone'
            check('front column course or shaft',[x,-1.12,z],[0,1,0],.78,{mat})
            check('rear column seen from behind',[x,1.14,z],[0,-1,0],.79,{mat})
    for x in (-.74,-.39,0,.39,.74):
        for z in (.30,1.2,2.2):
            check('clear axis through the whole porch',[x,-1.1,z],[0,1,0],2.38,None)
    # Shoot normal to the photographed soffit at the centre of each coffer.
    for s in range(6):
        a=pi*(s+.5)/6;xx=.954*cos(a);zz=2.51+.777*sin(a)
        for row in range(6):
            y=-.74+1.48*(row+.5)/6
            check('soffit centre within a coffer',[xx-.16*cos(a),y,zz-.16*sin(a)],
                  [cos(a),0,sin(a)],.24,{'recess boss'},.16,.013)
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
