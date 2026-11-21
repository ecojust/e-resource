from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-wu-residence-five-bat-garden-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import pi,cos,sin
    rows=[]
    def sample(label,origin,direction,materials,interval):
        hit=scene.ray(origin,direction,5.0)
        ok=hit is None if not materials else bool(hit and hit['material'] in materials and interval[0]<=hit['distance_m']<=interval[1])
        rows.append(dict(check=label,origin=origin,direction=direction,materials=materials,distance=interval,hit=hit,passed=ok))
    for x in [-.50,-.29,0,.29,.50]:
        for z in [.06,.44,1.13,1.81,2.04]:
            sample('open courtyard passage',[x,-1,z],[0,1,0],[],[])
    for side in (-1,1):
        for x in [.70,.74,.80]:
            sample('sandstone foot',[side*x,-1,.21],[0,1,0],['brown sandstone'],[.90,.95])
        for z in [.66,1.14,1.61]:
            sample('cut stone jamb bed',[side*.713,-1,z],[0,1,0],['brown sandstone'],[.959,.966])
            sample('plastered wall outside arch',[side*1.02,-1,z],[0,1,0],['warm plaster'],[.998,1.002])
    for angle in [.21,.47,.70,1.,1.28,pi/2,1.83,2.1,2.4,2.68,2.92]:
        for r,mat,interval in [(.8489,['carved pale stone'],[.946,.951]),(.889,['warm plaster'],[.998,1.002])]:
            sample('arched surround follows measured curve',[r*cos(angle),-1,1.96+r*sin(angle)],[0,1,0],mat,interval)
    for angle in (.17,.88,pi/2,pi-.88,pi-.17):
        ray=[cos(angle),0,sin(angle)]
        for y in [.265,.29]:
            sample('bat body or wing stands proud of intrados',[0,y,1.96],ray,['honey stone','carved pale stone'],[.528,.604])
        sample('plain soffit behind bat',[0,.045,1.96],ray,['honey stone'],[.605,.613])
    for x in [-1.29,-.94,-.58,0,.46,.77,1.28]:
        sample('carved stone beam at impost',[x,-1,3.74],[0,1,0],['carved eave beam','honey stone'],[.903,.924])
    for j in range(-8,9,2):
        x=j*.205
        sample('tile roll lifted above sloping bed',[x,-.29,5.0],[0,0,-1],['green glazed roll'],[.47,.78])
    return dict(passed=all(r['passed'] for r in rows),samples=rows)

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
