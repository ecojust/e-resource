from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-wuyi-154-octagonal-attic'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def shoot(u,v,mat,depth,label):
        x=(u-170)*.009;z=(321-v)*.009;hit=scene.ray([x,-.6,z],[0,1,0],1.3)
        good=not hit if mat is None else bool(hit and hit['material'] in mat and abs(hit['distance_m']-(depth+.6))<.003)
        samples.append(dict(feature=label,pixel=[u,v],expected_material=mat,depth=depth,hit=hit,passed=good))
    inner=[(146,195),(190,195),(216,221),(219,259),(190,287),(150,288),(121,261),(121,224)]
    outer=[(141,184),(195,183),(230,217),(232,264),(195,299),(145,301),(107,266),(106,220)]
    bricks=['oxblood brick','brown brick','terracotta brick','faded red brick']
    for i,(a,c) in enumerate(zip(outer,outer[1:]+outer[:1])):
        b=inner[i];d=inner[(i+1)%8]
        for j in range([5,6,4,6,6,6,5,6][i]):
            t=(j+.5)/[5,6,4,6,6,6,5,6][i]
            for s in (.38,.7):
                u=(a[0]+t*(c[0]-a[0]))*(1-s)+(b[0]+t*(d[0]-b[0]))*s
                v=(a[1]+t*(c[1]-a[1]))*(1-s)+(b[1]+t*(d[1]-b[1]))*s
                shoot(u,v,[bricks[(i+j)%4]],-.006,'individual voussoir on each of the eight edges')
    for u in [134,147,163,179,196,207]:
        shoot(u,243-(u-134)*.027,['dark sash'],.063,'continuous crosspiece')
        for v in (231,251):shoot(u,v,['interior shadow'],.147,'recess above and below crosspiece')
    for i in range(1,27):
        x=57+(i+.5)*7.65
        shoot(x,143,bricks,-.014,'tall first soldier course');shoot(x,129,bricks,-.018,'short second soldier course')
    for u in [88,134,182,230,264]:
        shoot(u,115,['eaves shadow'],-.11,'underside of roof fascia');shoot(u,121,['oxblood brick'],-.053,'projecting cornice')
    for uv in [(55,215),(278,225),(249,302)]:shoot(*uv,None,0,'outside visible wall and roof intersection')
    return dict(samples=samples,passed=all(s['passed'] for s in samples))

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
