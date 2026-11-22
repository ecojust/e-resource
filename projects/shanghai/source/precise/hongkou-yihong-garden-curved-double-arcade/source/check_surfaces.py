from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-yihong-garden-curved-double-arcade'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    from math import sin,cos,pi
    r=3.68
    rows=[]
    def sample(label,u,z,front,materials):
        t=u/r
        origin=[(r+.45)*sin(t),r-(r+.45)*cos(t),z]
        ray=[-sin(t),cos(t),0]
        hit=scene.ray(origin,ray,1.12)
        ok=(hit is None) if front is None else bool(hit and hit['material'] in materials and abs(hit['distance_m']-(.45+front))<.026)
        rows.append(dict(feature=label,developed_width_m=u,z_m=z,origin=origin,direction=ray,expected_depth_m=front,materials=materials,hit=hit,passed=ok))
    for i,c in enumerate((-1.01,1.01)):
        for spring in (1.66,4.42):
            for j in range(1,23):
                ang=(j+.5)*pi/23
                sample('red voussoir across the arch',c+.885*cos(ang),spring+.910*sin(ang),-.021,['brick ring','pale voussoir','deep voussoir'])
            for k in (-.6,-.25,.25,.60):
                sample('clear through arch head',c+k,spring+.18,None,[])
                sample('open gallery under head',c+k,spring-.34,None,[])
        for j in (2,3,5,7,8,11):
            u=c+j*.128-.768
            sample('iron upright in upper gallery',u,3.235,-.002,['balcony iron'])
            sample('open gap of iron balustrade',u+.053,3.235,None,[])
    for u in (-2.02,0,2.02):
        for s,f,m in ((.88,.012,'shaft stone'),(1.558,-.022,'limestone'),(1.63,-.048,'limestone'),(3.63,.012,'shaft stone'),(4.305,-.022,'limestone')):
            sample('stone pier and cap',u,s,f,[m])
    for i in range(17):
        u=-2.11+4.22*i/16
        sample('arc of balcony shelf',u,2.821,-.103,['limestone'])
        sample('dark edge of curved roof',u,5.667,-.134,['timber fascia'])
    return dict(samples=rows,passed=all(e['passed'] for e in rows))

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
