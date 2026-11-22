from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-meilun-west-twin-oval-cartouches'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos,sin,pi
    rows=[]
    def testface(angle,side):
        ca,sa=cos(angle),sin(angle)
        def hit(label,x,z,mat,d,tol=.008):
            x+=side*.283
            origin=[x*ca+.5*sa,x*sa-.5*ca,z]
            target=scene.ray(origin,[-sa,ca,0],1)
            rows.append(dict(feature=label,face=side,origin=origin,expected_material=mat,expected_depth=d,observed=target,passed=bool(target and target['material']==mat and abs(target['distance_m']-.5-d)<tol)))
        for x in [-.24,-.16,-.08,0,.08,.16,.24]:
            hit('first stone course',x,.06,'grey ashlar',0)
            hit('deep ashlar seam',x,.112,'mortar shadow',.045)
            hit('upper pier course',x,.20,'grey ashlar',-.002)
            hit('overhanging cap',x,.798,'grey ashlar',-.054)
        for theta in [.04,.53,1.11,2.10,2.50,3.12,3.67,4.14,5.16,5.78]:
            hit('raised elliptical frame',.124*cos(theta),.499+.169*sin(theta),'corded edge',-.052,.011)
        for x,z in [(0,.50),(.032,.503),(-.042,.494),(.032,.464),(0,.466),(-.033,.462)]:
            hit('convex blank in oval shield',x,z,'oval field',-.044,.009)
        hit('central flower boss',0,.528,'small flower',-.068)
        for x in [-.248,.242]:
            for z in [.319,.392,.481,.581,.661]:hit('blank stone beside foliage',x,z,'capital stone',-.009)
        for sign in [-1,1]:
            hit('top spiral boss',sign*.09,.691,'scroll ridge',-.046)
    testface(-pi/4,-1);testface(0,1)
    return {'samples':rows,'passed':all(row['passed']for row in rows)}

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
